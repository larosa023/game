package me.vrekt.oasis.asset.settings;

import com.badlogic.gdx.Input;
import com.badlogic.gdx.InputAdapter;

/**
 * Keys that work everywhere: F11 fullscreen (also Alt+Enter), F3 debug info.
 */
public final class GlobalHotkeys extends InputAdapter {

    private boolean altDown;

    @Override
    public boolean keyDown(int keycode) {
        if (keycode == Input.Keys.ALT_LEFT || keycode == Input.Keys.ALT_RIGHT) altDown = true;
        if (keycode == Input.Keys.F11 || (altDown && keycode == Input.Keys.ENTER)) {
            DisplaySettings.toggleFullscreen();
            return true;
        }
        if (keycode == Input.Keys.F3) {
            DisplaySettings.setShowFps(!OasisGameSettings.SHOW_FPS);
            return true;
        }
        return false;
    }

    @Override
    public boolean keyUp(int keycode) {
        if (keycode == Input.Keys.ALT_LEFT || keycode == Input.Keys.ALT_RIGHT) altDown = false;
        return false;
    }
}
