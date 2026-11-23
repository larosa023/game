package me.vrekt.oasis.questing.quests.mycelia;

import me.vrekt.oasis.GameManager;
import me.vrekt.oasis.entity.player.sp.PlayerSP;
import me.vrekt.oasis.gui.guis.hud.HudComponentType;
import me.vrekt.oasis.gui.guis.hud.components.HudNewQuestComponent;
import me.vrekt.oasis.item.Items;
import me.vrekt.oasis.item.weapons.magic.StaffOfEarthItem;
import me.vrekt.oasis.questing.Quest;
import me.vrekt.oasis.questing.QuestDifficulty;
import me.vrekt.oasis.questing.QuestObjective;
import me.vrekt.oasis.questing.QuestReward;
import me.vrekt.oasis.questing.QuestRewardType;
import me.vrekt.oasis.questing.quests.QuestType;

/**
 * The Mycelic Grove's quest: clear out Sporelings, gather mushrooms, find the hidden codex, head home.
 */
public final class SporesOfTheGroveQuest extends Quest {

    public static final int STEP_ENTER = 0, STEP_SPORELINGS = 1, STEP_MUSHROOMS = 2, STEP_CODEX = 3, STEP_RETURN = 4;
    public static final int SPORELINGS_NEEDED = 4, MUSHROOMS_NEEDED = 5;

    private int sporelingsDefeated, mushroomsGathered;

    public SporesOfTheGroveQuest() {
        super("Spores of the Grove", "The Mycelic Grove is overrun. Help the spore-folk and see what the forest hides.",
                QuestType.SPORES_OF_THE_GROVE,
                QuestDifficulty.BEGINNER);

        rewards.add(new QuestReward(QuestRewardType.XP, 120, QuestReward.XP_DESCRIPTOR));
        rewards.add(new QuestReward(QuestRewardType.ITEM, 1, StaffOfEarthItem.DESCRIPTOR));

        objectives.add(new QuestObjective("Step through the portal into the Mycelic Grove.", true));
        objectives.add(new QuestObjective("Defeat " + SPORELINGS_NEEDED + " Sporelings.", false));
        objectives.add(new QuestObjective("Gather " + MUSHROOMS_NEEDED + " mushrooms in the Grove.", false));
        objectives.add(new QuestObjective("Find what is hidden in the north-east corner.", false));
        objectives.add(new QuestObjective("Return to the village through the portal.", false));
    }

    private static SporesOfTheGroveQuest active(PlayerSP player) {
        return (SporesOfTheGroveQuest) player.getQuestManager().getQuest(QuestType.SPORES_OF_THE_GROVE);
    }

    /**
     * Start the quest the first time the player enters the Grove
     */
    public static void onEnterGrove(PlayerSP player) {
        if (player.getQuestManager().isQuestActive(QuestType.SPORES_OF_THE_GROVE)
                || player.getQuestManager().hasCompleted(QuestType.SPORES_OF_THE_GROVE)) return;

        final SporesOfTheGroveQuest quest = new SporesOfTheGroveQuest();
        player.getQuestManager().addActiveQuest(QuestType.SPORES_OF_THE_GROVE, quest);
        player.getQuestManager().advanceQuestIfOnStep(QuestType.SPORES_OF_THE_GROVE, STEP_ENTER);
        final HudNewQuestComponent component = GameManager.gui().getHudComponent().getComponent(HudComponentType.NEW_QUEST);
        if (component != null) component.showQuestAdded(quest);
    }

    public static void onSporelingDefeated(PlayerSP player) {
        final SporesOfTheGroveQuest quest = active(player);
        if (quest == null || quest.currentObjectiveStep() != STEP_SPORELINGS) return;
        if (++quest.sporelingsDefeated >= SPORELINGS_NEEDED) {
            player.getQuestManager().advanceQuestIfOnStep(QuestType.SPORES_OF_THE_GROVE, STEP_SPORELINGS);
        }
    }

    public static void onItemPickedUp(PlayerSP player, Items item) {
        final SporesOfTheGroveQuest quest = active(player);
        if (quest == null) return;
        if (item == Items.CRIMSON_CAP || item == Items.VERDANT_FUNGUS || item == Items.SILVER_SPORE) {
            quest.mushroomsGathered++;
            if (quest.currentObjectiveStep() == STEP_MUSHROOMS && quest.mushroomsGathered >= MUSHROOMS_NEEDED) {
                player.getQuestManager().advanceQuestIfOnStep(QuestType.SPORES_OF_THE_GROVE, STEP_MUSHROOMS);
            }
        } else if (item == Items.ARCANA_CODEX) {
            // finding the codex early still counts once the earlier steps are done
            quest.codexFound = true;
        }
        if (quest.codexFound) player.getQuestManager().advanceQuestIfOnStep(QuestType.SPORES_OF_THE_GROVE, STEP_CODEX);
    }

    private boolean codexFound;

    /**
     * The player left the Grove through a portal
     */
    public static void onReturnHome(PlayerSP player) {
        final SporesOfTheGroveQuest quest = active(player);
        if (quest == null) return;
        // mushrooms gathered before reaching that step still count
        if (quest.currentObjectiveStep() == STEP_MUSHROOMS && quest.mushroomsGathered >= MUSHROOMS_NEEDED) {
            player.getQuestManager().advanceQuestIfOnStep(QuestType.SPORES_OF_THE_GROVE, STEP_MUSHROOMS);
        }
        if (quest.currentObjectiveStep() == STEP_CODEX && quest.codexFound) {
            player.getQuestManager().advanceQuestIfOnStep(QuestType.SPORES_OF_THE_GROVE, STEP_CODEX);
        }
        if (player.getQuestManager().advanceQuestIfOnStep(QuestType.SPORES_OF_THE_GROVE, STEP_RETURN)) {
            player.getInventory().add(Items.STAFF_OF_EARTH, 1);
            player.getQuestManager().completeQuest(QuestType.SPORES_OF_THE_GROVE);
        }
    }
}
