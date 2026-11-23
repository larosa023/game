package me.vrekt.oasis.questing;

import me.vrekt.oasis.GameManager;
import me.vrekt.oasis.asset.sound.Sounds;
import me.vrekt.oasis.gui.GuiType;
import me.vrekt.oasis.questing.quests.QuestType;

import java.util.HashMap;
import java.util.Map;

/**
 * Handles the player questing system
 */
public final class PlayerQuestManager {

    // active player quests
    private final Map<QuestType, Quest> activeQuests = new HashMap<>();
    // quests the player has finished, so they are not offered again
    private final java.util.EnumSet<QuestType> completedQuests = java.util.EnumSet.noneOf(QuestType.class);
    private int completedQuestsAmount;

    public void addActiveQuest(QuestType type, Quest quest) {
        this.activeQuests.put(type, quest);
    }

    /**
     * Get a quest.
     *
     * @param type the type
     * @return the quest
     */
    public Quest getQuest(QuestType type) {
        return activeQuests.get(type);
    }

    /**
     * Advance an active quest
     *
     * @param type the type
     */
    public void advanceQuest(QuestType type) {
        activeQuests.get(type).updateQuestObjectiveAndUnlockNext();
    }

    public boolean isQuestActive(QuestType type) {
        return activeQuests.containsKey(type);
    }

    public int completedQuestsAmount() {
        return completedQuestsAmount;
    }

    /**
     * Complete the quest
     *
     * @param type the type
     */
    public void completeQuest(QuestType type) {
        final Quest quest = activeQuests.remove(type);
        completedQuests.add(type);
        if (quest != null) {
            GameManager.gui().hideGui(GuiType.DIALOG);
            GameManager.gui().getCompletedQuestComponent().showQuestCompleted(quest);
            GameManager.playSound(Sounds.QUEST_COMPLETED, 0.2f, 1.0f, 0.0f);
        }

        completedQuestsAmount++;
    }

    public boolean hasCompleted(QuestType type) {
        return completedQuests.contains(type);
    }

    public java.util.Set<QuestType> completedQuests() {
        return completedQuests;
    }

    /**
     * Advance a quest only if it is active and currently on the given objective step
     *
     * @param type the quest
     * @param step the objective index that should be completed
     * @return {@code true} if it advanced
     */
    public boolean advanceQuestIfOnStep(QuestType type, int step) {
        final Quest quest = activeQuests.get(type);
        if (quest == null || quest.currentObjectiveStep() != step) return false;
        quest.updateQuestObjectiveAndUnlockNext();
        GameManager.playSound(Sounds.QUEST_ADDED, 0.15f, 1.2f, 0.0f);
        return true;
    }

    public Map<QuestType, Quest> getActiveQuests() {
        return activeQuests;
    }
}
