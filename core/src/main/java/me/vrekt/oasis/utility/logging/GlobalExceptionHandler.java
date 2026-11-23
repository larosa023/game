package me.vrekt.oasis.utility.logging;

import me.vrekt.oasis.GameManager;

public final class GlobalExceptionHandler implements Thread.UncaughtExceptionHandler {

    @Override
    public void uncaughtException(Thread thread, Throwable exception) {
        GameLogging.exceptionThrown("ExceptionHandler", "Exception caught in thread %s", exception, thread.getName());
        writeCrashLog(thread, exception);
        try {
            GameManager.game().dispose();
        } catch (Throwable ignored) {
        }
        System.exit(-1);
    }

    /**
     * Write the crash to %APPDATA%\\Oasis\\crash.log (or ~/.oasis/crash.log) so it can be shared.
     */
    public static void writeCrashLog(Thread thread, Throwable exception) {
        try {
            final java.nio.file.Path dir = me.vrekt.oasis.save.SaveManager.SAVE_DIR.getParent();
            java.nio.file.Files.createDirectories(dir);
            final java.io.StringWriter out = new java.io.StringWriter();
            out.write("Oasis crashed at " + java.time.LocalDateTime.now() + " (version "
                    + me.vrekt.oasis.update.GameUpdater.currentVersion() + ", thread " + thread.getName() + ")\n");
            out.write(System.getProperty("os.name") + " / Java " + System.getProperty("java.version") + "\n\n");
            exception.printStackTrace(new java.io.PrintWriter(out));
            java.nio.file.Files.writeString(dir.resolve("crash.log"), out.toString());
        } catch (Throwable ignored) {
        }
    }

}
