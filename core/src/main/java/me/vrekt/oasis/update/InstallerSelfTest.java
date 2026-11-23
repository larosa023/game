package me.vrekt.oasis.update;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.concurrent.TimeUnit;

/**
 * Exercises the Windows update installer script end to end without the game.
 * Run by the release build on a Windows machine; exits non-zero on failure.
 */
public final class InstallerSelfTest {

    public static void main(String[] args) throws Exception {
        final Path root = Files.createTempDirectory("oasis-installer-test");
        final Path install = Files.createDirectories(root.resolve("install"));
        final Path source = Files.createDirectories(root.resolve("work").resolve("Oasis"));

        // "installed" game: old files plus a player file the update must not remove
        Files.writeString(install.resolve("app.txt"), "old");
        Files.writeString(install.resolve("keep-me.txt"), "player data");
        // "new" release: a real exe so Start-Process can launch it, plus updated files
        final Path dummyExe = Paths.get(System.getenv("SystemRoot"), "System32", "whoami.exe");
        Files.copy(dummyExe, source.resolve("Oasis.exe"));
        Files.createDirectories(source.resolve("app"));
        Files.writeString(source.resolve("app.txt"), "new");
        Files.writeString(source.resolve("app").resolve("Oasis.cfg"), "cfg");

        // stand-in for the running game: a process that lives a few seconds
        final Process fakeGame = new ProcessBuilder("ping", "-n", "4", "127.0.0.1").start();

        final Path script = root.resolve("work").resolve("install-update.ps1");
        Files.writeString(script, GameUpdater.installerScript(fakeGame.pid(), source, install, install.resolve("Oasis.exe"), root.resolve("work")));

        final Process installer = new ProcessBuilder("powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script.toString())
                .inheritIO().start();
        if (!installer.waitFor(120, TimeUnit.SECONDS)) fail("installer timed out");
        if (fakeGame.isAlive()) fail("installer did not wait for the game to exit");

        expect(Files.readString(install.resolve("app.txt")).equals("new"), "updated file replaced");
        expect(Files.exists(install.resolve("app").resolve("Oasis.cfg")), "new folder copied");
        expect(Files.exists(install.resolve("Oasis.exe")), "exe copied");
        expect(Files.readString(install.resolve("keep-me.txt")).equals("player data"), "player file kept");
        expect(!Files.exists(root.resolve("work")), "temp folder cleaned up");
        System.out.println("INSTALLER SELF TEST PASSED");
    }

    private static void expect(boolean condition, String what) {
        System.out.println((condition ? "ok   " : "FAIL ") + what);
        if (!condition) fail(what);
    }

    private static void fail(String why) {
        System.err.println("INSTALLER SELF TEST FAILED: " + why);
        System.exit(1);
    }
}
