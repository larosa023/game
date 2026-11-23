package me.vrekt.oasis.world.obj.interaction.impl.misc;

import com.badlogic.gdx.maps.MapObject;
import me.vrekt.oasis.GameManager;
import me.vrekt.oasis.asset.sound.Sounds;
import me.vrekt.oasis.utility.tiled.TiledMapLoader;
import me.vrekt.oasis.world.obj.interaction.WorldInteractionType;
import me.vrekt.oasis.world.obj.interaction.impl.KeyableAbstractInteractableMouseObject;

/**
 * A portal that sends the player to another world when they press E.
 * Map properties: target_world (int world id), portal_text (prompt shown, optional)
 */
public final class PortalInteraction extends KeyableAbstractInteractableMouseObject {

    private final int targetWorld;
    private final String text;

    public PortalInteraction(MapObject object) {
        super(WorldInteractionType.PORTAL);
        this.targetWorld = TiledMapLoader.ofInt(object, "target_world", 0);
        final String prompt = TiledMapLoader.ofString(object, "portal_text");
        this.text = prompt == null ? "Travel" : prompt;
        this.interactionDelay = 2.0f;
        this.shouldSave = false;
    }

    @Override
    public String getInteractionText() {
        return text;
    }

    @Override
    public void interact() {
        lastInteraction = GameManager.tick();
        GameManager.playSound(Sounds.TELEPORT, 0.1f, -3.0f, 0.0f);
        GameManager.gui().getInteractionsComponent().hide();
        if (targetWorld == 0) me.vrekt.oasis.questing.quests.mycelia.SporesOfTheGroveQuest.onReturnHome(world.player());
        GameManager.game().worldManager().transferTo(world.player(), targetWorld);
    }
}
