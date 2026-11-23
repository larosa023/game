package me.vrekt.oasis.ui;

import com.badlogic.gdx.Gdx;
import com.badlogic.gdx.ScreenAdapter;
import com.badlogic.gdx.graphics.Color;
import com.badlogic.gdx.graphics.OrthographicCamera;
import com.badlogic.gdx.graphics.Texture;
import com.badlogic.gdx.graphics.g2d.SpriteBatch;
import com.badlogic.gdx.scenes.scene2d.Actor;
import com.badlogic.gdx.scenes.scene2d.InputEvent;
import com.badlogic.gdx.scenes.scene2d.Stage;
import com.badlogic.gdx.scenes.scene2d.ui.Label;
import com.badlogic.gdx.scenes.scene2d.utils.ClickListener;
import com.badlogic.gdx.scenes.scene2d.utils.NinePatchDrawable;
import com.badlogic.gdx.utils.ScreenUtils;
import com.badlogic.gdx.utils.viewport.ScreenViewport;
import com.kotcrab.vis.ui.widget.VisImage;
import com.kotcrab.vis.ui.widget.VisImageTextButton;
import com.kotcrab.vis.ui.widget.VisLabel;
import com.kotcrab.vis.ui.widget.VisTable;
import me.vrekt.oasis.OasisGame;
import me.vrekt.oasis.asset.settings.OasisGameSettings;
import me.vrekt.oasis.asset.sound.Sounds;
import me.vrekt.oasis.gui.Styles;
import me.vrekt.oasis.save.GameSaveProperties;
import me.vrekt.oasis.save.GameSaveSlotProperty;
import me.vrekt.oasis.save.SaveManager;
import me.vrekt.oasis.update.GameUpdater;
import me.vrekt.oasis.utility.logging.GameLogging;

/**
 * The main menu of the game
 */
public final class OasisMainMenu extends ScreenAdapter {

    private static final Color HOVER_COLOR = new Color(64 / 255f, 64 / 255f, 64 / 255f, 1);

    private final SpriteBatch parallaxBatch;
    private final OrthographicCamera parallaxCamera;
    private final Texture parallaxTexture;

    private final OasisGame game;
    private final Stage stage;
    // the main UI components
    private final VisTable rootTable;
    // holds elements of the loading game UI
    private final VisTable loadGameTable;
    // holds the "update available" button when there is one
    private final VisTable updateRow = new VisTable();
    private GameUpdater updater;
    private boolean updating;

    public OasisMainMenu(OasisGame game) {
        this.game = game;

        parallaxBatch = new SpriteBatch();
        parallaxCamera = new OrthographicCamera(Gdx.graphics.getWidth(), Gdx.graphics.getHeight());
        parallaxTexture = new Texture(Gdx.files.internal("ui/parallax/main_menu_background.png"));
        parallaxTexture.setWrap(Texture.TextureWrap.MirroredRepeat, Texture.TextureWrap.ClampToEdge);

        // offset camera position, so we can see the higher part of the parallax demo
        parallaxCamera.position.y = -100;

        this.stage = new Stage(new ScreenViewport());
        this.rootTable = new VisTable();
        this.loadGameTable = new VisTable();
        this.rootTable.setFillParent(true);
        this.loadGameTable.setFillParent(true);

        // add UI components
        rootTable.add(new VisImage(game.getLogoTexture()))
                .size(game.getLogoTexture().getWidth() * 2f, game.getLogoTexture().getHeight() * 2f)
                .padBottom(12f);
        rootTable.row();

        initializeMainComponents(Styles.getImageTextButtonStyle());
        initializeLoadGameComponents(Styles.getThemePadded(), Styles.getImageTextButtonStyle());

        stage.addActor(rootTable);
    }

    @Override
    public void show() {
        game.multiplexer().addProcessor(stage);
        me.vrekt.oasis.asset.sound.MusicPlayer.get().play(me.vrekt.oasis.asset.sound.MusicPlayer.Track.TITLE);
    }

    @Override
    public void resize(int width, int height) {
        ((ScreenViewport) stage.getViewport()).setUnitsPerPixel(OasisGameSettings.uiUnitsPerPixel(height));
        stage.getViewport().update(width, height, true);
        parallaxCamera.setToOrtho(false, width * OasisGameSettings.uiUnitsPerPixel(height), height * OasisGameSettings.uiUnitsPerPixel(height));
        parallaxCamera.position.y = -100;
    }

    @Override
    public void hide() {
        game.multiplexer().removeProcessor(stage);
        dispose();
    }

    /**
     * Initialize main UI components
     */
    private void initializeMainComponents(VisImageTextButton.VisImageTextButtonStyle style) {
        final VisImageTextButton newGameButton = new VisImageTextButton("New Game", style);
        final VisImageTextButton joinServerButton = new VisImageTextButton("Join Server", style);
        final VisImageTextButton loadGameButton = new VisImageTextButton("Load Game", style);
        final VisImageTextButton quitGameButton = new VisImageTextButton("Quit Game", style);

        rootTable.add(newGameButton).width(150).padBottom(4f);
        rootTable.row();
        rootTable.add(loadGameButton).width(150).padBottom(4f);
        rootTable.row();
        rootTable.add(joinServerButton).width(150).padBottom(4f);
        rootTable.row();
        rootTable.add(quitGameButton).width(150);
        rootTable.row();
        rootTable.add(updateRow).padTop(8f);
        rootTable.row();
        rootTable.add(new VisLabel("Version " + GameUpdater.currentVersion(), Styles.getMediumWhiteMipMapped())).padTop(6f);

        checkForUpdates(style);

        assignClickAction(newGameButton, game::enterNewGame);
        assignClickAction(joinServerButton, game::joinLanGame);

        // show load game UI
        assignClickAction(loadGameButton, () -> {
            stage.clear();
            stage.addActor(loadGameTable);
        });

        assignClickAction(quitGameButton, () -> System.exit(0));
    }

    /**
     * Check GitHub for a newer version and, if there is one, show an update button.
     */
    private void checkForUpdates(VisImageTextButton.VisImageTextButtonStyle style) {
        try {
            updater = new GameUpdater();
        } catch (Throwable throwable) {
            // never let the updater stop the game from starting
            GameLogging.exceptionThrown("OasisMainMenu", "Updater unavailable", throwable);
            return;
        }
        updater.checkAsync().thenAccept(update -> {
            if (update == null) return;
            Gdx.app.postRunnable(() -> showUpdateButton(update, style));
        });
    }

    private void showUpdateButton(GameUpdater.UpdateInfo update, VisImageTextButton.VisImageTextButtonStyle style) {
        final VisImageTextButton button = new VisImageTextButton("Update to v" + update.version(), style);
        button.getLabel().setColor(Color.GOLD);
        updateRow.clear();
        updateRow.add(button).width(190);

        assignClickAction(button, () -> {
            if (updating) return;
            updating = true;
            button.setText("Downloading 0%");
            updater.downloadAndInstall(update, progress ->
                            Gdx.app.postRunnable(() -> button.setText("Downloading " + (int) (progress * 100) + "%")))
                    .whenComplete((ignored, error) -> Gdx.app.postRunnable(() -> {
                        if (error != null) {
                            GameLogging.exceptionThrown("OasisMainMenu", "Update failed", error);
                            button.setText("Update failed - retry");
                            updating = false;
                        } else {
                            button.setText("Restarting...");
                            // the installer waits for us to close, swaps the files, and relaunches
                            Gdx.app.exit();
                        }
                    }));
        });
    }

    /**
     * Initialize load game component table
     *
     * @param theme the theme
     * @param style the style
     */
    private void initializeLoadGameComponents(NinePatchDrawable theme, VisImageTextButton.VisImageTextButtonStyle style) {
        SaveManager.readSaveGameProperties(); // read if we haven't already

        final Label.LabelStyle labelStyle = new Label.LabelStyle(game.asset().getMedium(), Color.WHITE);
        final GameSaveProperties properties = SaveManager.getProperties();

        if (properties.hasSaveSlot(1)) addSlotTableComponent(properties.getSaveSlotProperty(1), theme, labelStyle);
        if (properties.hasSaveSlot(2)) addSlotTableComponent(properties.getSaveSlotProperty(2), theme, labelStyle);
        if (properties.hasSaveSlot(3)) addSlotTableComponent(properties.getSaveSlotProperty(3), theme, labelStyle);

        // if no saves just display that.
        if (!properties.hasAnySaveSlots()) {
            loadGameTable.add(new VisLabel("No Save Games Available!", new Label.LabelStyle(game.asset().getLarge(), Color.WHITE)));
            loadGameTable.row();
        }

        final VisImageTextButton backButton = new VisImageTextButton("Go Back", style);
        loadGameTable.add(backButton).fillX();

        // go back
        assignClickAction(backButton, () -> {
            stage.clear();
            stage.addActor(rootTable);
        });
    }

    /**
     * Add a save slot table component to the root
     *
     * @param properties the properties
     * @param theme      the theme
     * @param style      the style
     */
    private void addSlotTableComponent(GameSaveSlotProperty properties, NinePatchDrawable theme, Label.LabelStyle style) {
        final VisTable root = new VisTable();
        final VisImage saveImage = new VisImage(game.asset().get("secondwind_artifact"));
        final VisLabel saveName = new VisLabel(properties.name(), style);
        final VisLabel progress = new VisLabel(properties.progress() + "", style);
        final VisLabel dateSaved = new VisLabel(properties.date(), style);

        root.setBackground(theme);
        root.add(saveImage);

        final VisTable table = new VisTable();
        table.add(saveName).left();
        table.row();
        table.add(progress).left();
        table.row();
        table.add(dateSaved).left();
        root.add(table).padLeft(12f);

        loadGameTable.add(root).padBottom(6f);
        loadGameTable.row();

        root.addListener(new ClickListener() {
            @Override
            public void clicked(InputEvent event, float x, float y) {
                game.loadSaveGame(properties.slot());
            }

            @Override
            public void enter(InputEvent event, float x, float y, int pointer, Actor fromActor) {
                root.setColor(HOVER_COLOR);
                game.sounds().play(Sounds.BUTTON_HOVER, 0.8f, false);
            }

            @Override
            public void exit(InputEvent event, float x, float y, int pointer, Actor toActor) {
                root.setColor(Color.WHITE);
            }
        });

    }

    /**
     * Assign click action to an actor
     *
     * @param actor  the actor
     * @param action the action to run
     */
    private void assignClickAction(Actor actor, Runnable action) {
        actor.addListener(new ClickListener() {
            @Override
            public void clicked(InputEvent event, float x, float y) {
                action.run();
            }

            @Override
            public void enter(InputEvent event, float x, float y, int pointer, Actor fromActor) {
                game.sounds().play(Sounds.BUTTON_HOVER, 0.8f, false);
            }
        });
    }

    @Override
    public void render(float delta) {
        ScreenUtils.clear(1, 1, 1, 1);

        // increment camera position and scroll along
        parallaxCamera.position.x += 100 * delta;
        parallaxCamera.update();

        // render parallax
        parallaxBatch.setProjectionMatrix(parallaxCamera.combined);
        parallaxBatch.begin();
        renderBackground();
        parallaxBatch.end();

        // render stage afterward so elements are on top
        stage.act();
        stage.draw();
    }

    /**
     * Render the background of the main menu
     * Partially adapted from <a href="https://ailurux.github.io/ParallaxLibgdx/">...</a>
     */
    private void renderBackground() {
        final float originX = parallaxCamera.position.x - parallaxCamera.viewportWidth / 2f;
        final float originY = parallaxCamera.position.y - parallaxCamera.viewportHeight / 2f;

        final int x = (int) (parallaxCamera.position.x) % parallaxTexture.getWidth();
        final int y = (int) (parallaxCamera.position.y) % parallaxTexture.getHeight();

        parallaxBatch.draw(parallaxTexture,
                originX, originY, originX, originY,
                parallaxCamera.viewportWidth, parallaxTexture.getHeight(),
                1.0f,
                1.0f,
                0.0f,
                x,
                y,
                (int) parallaxCamera.viewportWidth,
                parallaxTexture.getHeight(),
                false,
                false);
    }

    @Override
    public void dispose() {
        stage.dispose();
        parallaxBatch.dispose();
        parallaxTexture.dispose();
    }
}
