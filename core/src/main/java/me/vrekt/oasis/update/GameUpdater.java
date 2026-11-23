package me.vrekt.oasis.update;

import com.badlogic.gdx.Gdx;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import me.vrekt.oasis.utility.logging.GameLogging;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.time.Duration;
import java.util.concurrent.CompletableFuture;
import java.util.function.Consumer;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

/**
 * Checks GitHub for a newer release of the game and installs it.
 * <p>
 * Installing works by downloading the release zip, extracting it next to the
 * running game, and handing off to a small PowerShell script that waits for the
 * game to close, copies the new files over the install folder, and starts the game again.
 */
public final class GameUpdater {

    public static final String REPOSITORY = "larosa023/game";
    private static final String LATEST_RELEASE = "https://api.github.com/repos/" + REPOSITORY + "/releases/latest";
    private static final String ASSET_NAME = "Oasis-windows.zip";

    private static String currentVersion;

    private final HttpClient client = HttpClient.newBuilder()
            .followRedirects(HttpClient.Redirect.ALWAYS)
            .connectTimeout(Duration.ofSeconds(10))
            .build();

    /**
     * Information about an available update
     *
     * @param version     the new version
     * @param downloadUrl where to download the zip
     * @param notes       release notes
     */
    public record UpdateInfo(String version, String downloadUrl, String notes) {
    }

    /**
     * @return the version of this build, from version.txt written by the release build, or "dev"
     */
    public static String currentVersion() {
        if (currentVersion == null) {
            currentVersion = "dev";
            try {
                if (Gdx.files != null && Gdx.files.internal("version.txt").exists()) {
                    currentVersion = Gdx.files.internal("version.txt").readString("UTF-8").trim();
                }
            } catch (Exception exception) {
                GameLogging.warn("GameUpdater", "Could not read version.txt: %s", exception.getMessage());
            }
        }
        return currentVersion;
    }

    /**
     * @return the path of the running Oasis.exe, or {@code null} if this isn't a packaged Windows build
     */
    public static Path installedExecutable() {
        final String appPath = System.getProperty("jpackage.app-path");
        if (appPath == null) return null;
        if (!System.getProperty("os.name", "").toLowerCase().contains("win")) return null;
        return Paths.get(appPath);
    }

    /**
     * @return {@code true} if this build is able to update itself
     */
    public static boolean canSelfUpdate() {
        return installedExecutable() != null && !"dev".equals(currentVersion());
    }

    /**
     * Compare two versions like 1.0.12 and 1.0.9
     *
     * @return positive if a is newer than b
     */
    public static int compareVersions(String a, String b) {
        final String[] pa = a.replaceFirst("^[vV]", "").split("[.\\-]");
        final String[] pb = b.replaceFirst("^[vV]", "").split("[.\\-]");
        for (int i = 0; i < Math.max(pa.length, pb.length); i++) {
            final int x = i < pa.length ? parse(pa[i]) : 0;
            final int y = i < pb.length ? parse(pb[i]) : 0;
            if (x != y) return Integer.compare(x, y);
        }
        return 0;
    }

    private static int parse(String part) {
        try {
            return Integer.parseInt(part.replaceAll("\\D", ""));
        } catch (NumberFormatException exception) {
            return 0;
        }
    }

    /**
     * Check for an update in the background.
     *
     * @return a future with the update, or {@code null} if up to date / unavailable
     */
    public CompletableFuture<UpdateInfo> checkAsync() {
        if (!canSelfUpdate()) return CompletableFuture.completedFuture(null);

        final HttpRequest request = HttpRequest.newBuilder(URI.create(LATEST_RELEASE))
                .header("Accept", "application/vnd.github+json")
                .header("User-Agent", "Oasis-Game-Updater")
                .timeout(Duration.ofSeconds(15))
                .GET()
                .build();

        return client.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                .thenApply(response -> {
                    if (response.statusCode() != 200) {
                        GameLogging.warn("GameUpdater", "Update check returned HTTP %d", response.statusCode());
                        return null;
                    }
                    return parseRelease(response.body());
                })
                .exceptionally(throwable -> {
                    GameLogging.warn("GameUpdater", "Update check failed: %s", throwable.getMessage());
                    return null;
                });
    }

    private UpdateInfo parseRelease(String body) {
        final JsonObject release = JsonParser.parseString(body).getAsJsonObject();
        final String tag = release.get("tag_name").getAsString();
        if (compareVersions(tag, currentVersion()) <= 0) return null;

        final JsonArray assets = release.getAsJsonArray("assets");
        for (JsonElement element : assets) {
            final JsonObject asset = element.getAsJsonObject();
            if (ASSET_NAME.equals(asset.get("name").getAsString())) {
                final String notes = release.has("body") && !release.get("body").isJsonNull() ? release.get("body").getAsString() : "";
                return new UpdateInfo(tag.replaceFirst("^[vV]", ""), asset.get("browser_download_url").getAsString(), notes);
            }
        }
        return null;
    }

    /**
     * Download and stage the update, then start the installer script.
     * After this completes successfully the game should exit so the files can be replaced.
     *
     * @param update   the update
     * @param progress receives 0..1 download progress (called from a background thread)
     * @return future completing when the installer has been launched
     */
    public CompletableFuture<Void> downloadAndInstall(UpdateInfo update, Consumer<Float> progress) {
        return CompletableFuture.runAsync(() -> {
            try {
                final Path exe = installedExecutable();
                if (exe == null) throw new IllegalStateException("Not a packaged build");
                final Path installDir = exe.getParent();

                final Path work = Files.createTempDirectory("oasis-update-");
                final Path zip = work.resolve(ASSET_NAME);
                download(update.downloadUrl(), zip, progress);

                final Path extracted = work.resolve("extracted");
                unzip(zip, extracted);

                // the zip contains an "Oasis" folder with Oasis.exe inside
                Path source = extracted.resolve("Oasis");
                if (!Files.exists(source.resolve(exe.getFileName()))) source = extracted;
                if (!Files.exists(source.resolve(exe.getFileName()))) {
                    throw new IOException("Downloaded update does not contain " + exe.getFileName());
                }

                final Path script = work.resolve("install-update.ps1");
                Files.writeString(script, installerScript(ProcessHandle.current().pid(), source, installDir, exe, work), StandardCharsets.UTF_8);

                new ProcessBuilder("powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                        "-WindowStyle", "Hidden", "-File", script.toString())
                        .directory(work.toFile())
                        .start();
                GameLogging.info("GameUpdater", "Installer started for version %s", update.version());
            } catch (Exception exception) {
                throw new RuntimeException(exception);
            }
        });
    }

    private void download(String url, Path target, Consumer<Float> progress) throws IOException, InterruptedException {
        final HttpRequest request = HttpRequest.newBuilder(URI.create(url))
                .header("User-Agent", "Oasis-Game-Updater")
                .GET()
                .build();
        final HttpResponse<InputStream> response = client.send(request, HttpResponse.BodyHandlers.ofInputStream());
        if (response.statusCode() != 200) throw new IOException("Download failed: HTTP " + response.statusCode());

        final long total = response.headers().firstValueAsLong("Content-Length").orElse(-1);
        try (InputStream in = response.body(); OutputStream out = Files.newOutputStream(target)) {
            final byte[] buffer = new byte[64 * 1024];
            long read = 0;
            int n;
            while ((n = in.read(buffer)) != -1) {
                out.write(buffer, 0, n);
                read += n;
                if (total > 0) progress.accept((float) read / total);
            }
        }
        progress.accept(1f);
    }

    private void unzip(Path zip, Path destination) throws IOException {
        Files.createDirectories(destination);
        try (ZipInputStream in = new ZipInputStream(Files.newInputStream(zip))) {
            ZipEntry entry;
            while ((entry = in.getNextEntry()) != null) {
                final Path out = destination.resolve(entry.getName().replace('\\', '/')).normalize();
                if (!out.startsWith(destination)) throw new IOException("Bad zip entry: " + entry.getName());
                if (entry.isDirectory()) {
                    Files.createDirectories(out);
                } else {
                    Files.createDirectories(out.getParent());
                    Files.copy(in, out, StandardCopyOption.REPLACE_EXISTING);
                }
            }
        }
    }

    static String quote(Path path) {
        return "'" + path.toString().replace("'", "''") + "'";
    }

    static String installerScript(long pid, Path source, Path installDir, Path exe, Path work) {
        return String.join("\r\n",
                "$ErrorActionPreference = 'SilentlyContinue'",
                "Wait-Process -Id " + pid + " -Timeout 60",
                "Start-Sleep -Milliseconds 500",
                "$src = " + quote(source),
                "$dst = " + quote(installDir),
                "# /E copies everything (never deletes), so nothing of the player's is removed",
                "robocopy $src $dst /E /R:10 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null",
                "Start-Process -FilePath " + quote(exe) + " -WorkingDirectory $dst",
                "Start-Sleep -Seconds 5",
                "Remove-Item -Recurse -Force " + quote(work),
                "");
    }
}
