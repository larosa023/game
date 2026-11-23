package me.vrekt.oasis.asset.settings;

import com.badlogic.gdx.Gdx;
import com.badlogic.gdx.Graphics;
import com.badlogic.gdx.Preferences;

/**
 * Settings that belong to the player's computer rather than a save game: fullscreen and the debug overlay.
 */
public final class DisplaySettings {

    private static final String PREFS = "oasis-display";
    private static final int WINDOWED_WIDTH = 1280, WINDOWED_HEIGHT = 720;

    private static Preferences prefs() {
        return Gdx.app.getPreferences(PREFS);
    }

    /**
     * Apply what was saved last time
     */
    public static void applySaved() {
        OasisGameSettings.SHOW_FPS = prefs().getBoolean("show_fps", false);
        if (prefs().getBoolean("fullscreen", false)) setFullscreen(true);
    }

    public static boolean isFullscreen() {
        return Gdx.graphics.isFullscreen();
    }

    public static void setFullscreen(boolean fullscreen) {
        if (fullscreen) {
            final Graphics.DisplayMode mode = Gdx.graphics.getDisplayMode();
            Gdx.graphics.setFullscreenMode(mode);
        } else {
            Gdx.graphics.setWindowedMode(WINDOWED_WIDTH, WINDOWED_HEIGHT);
        }
        prefs().putBoolean("fullscreen", fullscreen).flush();
    }

    public static void toggleFullscreen() {
        setFullscreen(!isFullscreen());
    }

    /**
     * @return music volume 0..1 (default 0.6)
     */
    public static float musicVolume() {
        return prefs().getFloat("music_volume", 0.6f);
    }

    public static void setMusicVolume(float volume) {
        prefs().putFloat("music_volume", Math.max(0f, Math.min(1f, volume))).flush();
        me.vrekt.oasis.asset.sound.MusicPlayer.get().refreshVolume();
    }

    public static void setShowFps(boolean show) {
        OasisGameSettings.SHOW_FPS = show;
        prefs().putBoolean("show_fps", show).flush();
    }
}
