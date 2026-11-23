package me.vrekt.oasis.update;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.ArrayList;
import java.util.List;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;

/**
 * Run by the release build with the packaged (trimmed) Java runtime. Makes sure every game class
 * can resolve the Java classes it uses, and that HTTPS works for the updater. Exits non-zero on failure.
 */
public final class RuntimeSelfTest {

    public static void main(String[] args) throws Exception {
        final List<String> problems = new ArrayList<>();
        int checked = 0;
        try (JarFile jar = new JarFile(args[0])) {
            for (JarEntry entry : java.util.Collections.list(jar.entries())) {
                final String name = entry.getName();
                if (!name.startsWith("me/vrekt/") || !name.endsWith(".class")) continue;
                final String cls = name.substring(0, name.length() - 6).replace('/', '.');
                try {
                    final Class<?> c = Class.forName(cls, false, RuntimeSelfTest.class.getClassLoader());
                    c.getDeclaredFields();
                    c.getDeclaredMethods();
                    c.getDeclaredConstructors();
                    checked++;
                } catch (Throwable throwable) {
                    final String missing = String.valueOf(throwable.getMessage());
                    // only the Java runtime itself is our concern here; game libraries are all in the jar
                    if (missing.startsWith("java/") || missing.startsWith("javax/") || missing.startsWith("jdk/")
                            || missing.startsWith("java.") || missing.startsWith("javax.") || missing.startsWith("jdk.")) {
                        problems.add(cls + " -> " + throwable);
                    }
                }
            }
        }
        System.out.println("Checked " + checked + " game classes");

        final HttpResponse<String> response = HttpClient.newHttpClient().send(
                HttpRequest.newBuilder(URI.create("https://api.github.com/repos/" + GameUpdater.REPOSITORY))
                        .header("User-Agent", "Oasis-Runtime-Self-Test").build(),
                HttpResponse.BodyHandlers.ofString());
        System.out.println("HTTPS to GitHub: HTTP " + response.statusCode());
        if (response.statusCode() >= 500) problems.add("GitHub API returned " + response.statusCode());

        if (!problems.isEmpty()) {
            problems.forEach(p -> System.err.println("MISSING: " + p));
            System.err.println("RUNTIME SELF TEST FAILED");
            System.exit(1);
        }
        System.out.println("RUNTIME SELF TEST PASSED");
    }
}
