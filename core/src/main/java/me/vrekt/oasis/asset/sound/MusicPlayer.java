package me.vrekt.oasis.asset.sound;

import com.badlogic.gdx.Gdx;
import com.badlogic.gdx.audio.Music;
import com.badlogic.gdx.utils.Disposable;
import me.vrekt.oasis.asset.settings.DisplaySettings;
import me.vrekt.oasis.utility.logging.GameLogging;

import java.util.EnumMap;

/**
 * Background music with smooth cross-fades between tracks.
 */
public final class MusicPlayer implements Disposable {

    public enum Track {
        TITLE("sound/music/title.wav"),
        VILLAGE("sound/music/village.wav"),
        GROVE("sound/music/grove.wav");

        private final String path;

        Track(String path) {
            this.path = path;
        }
    }

    private static final float FADE_SECONDS = 1.5f;
    private static MusicPlayer instance;

    private final EnumMap<Track, Music> loaded = new EnumMap<>(Track.class);
    private Music current, fadingOut;
    private Track currentTrack;
    private float fade = 1f;

    public static MusicPlayer get() {
        if (instance == null) instance = new MusicPlayer();
        return instance;
    }

    private Music load(Track track) {
        return loaded.computeIfAbsent(track, t -> {
            try {
                final Music music = Gdx.audio.newMusic(Gdx.files.internal(t.path));
                music.setLooping(true);
                return music;
            } catch (Exception exception) {
                GameLogging.exceptionThrown("MusicPlayer", "Failed to load %s", exception, t.path);
                return null;
            }
        });
    }

    /**
     * Play a track (cross-fades from whatever is playing). Does nothing if it's already playing.
     */
    public void play(Track track) {
        if (track == currentTrack) return;
        final Music next = load(track);
        if (next == null) return;

        if (fadingOut != null) fadingOut.stop();
        fadingOut = current;
        current = next;
        currentTrack = track;
        fade = 0f;
        current.setVolume(0f);
        current.play();
    }

    /**
     * Apply a volume change right away
     */
    public void refreshVolume() {
        if (current != null) current.setVolume(fade * DisplaySettings.musicVolume());
    }

    /**
     * Advance fades; call every frame
     */
    public void update(float delta) {
        if (fade < 1f) {
            fade = Math.min(1f, fade + delta / FADE_SECONDS);
            final float volume = DisplaySettings.musicVolume();
            if (current != null) current.setVolume(fade * volume);
            if (fadingOut != null) {
                fadingOut.setVolume((1f - fade) * volume);
                if (fade >= 1f) {
                    fadingOut.stop();
                    fadingOut = null;
                }
            }
        }
    }

    @Override
    public void dispose() {
        loaded.values().forEach(m -> {
            if (m != null) m.dispose();
        });
        loaded.clear();
    }
}
