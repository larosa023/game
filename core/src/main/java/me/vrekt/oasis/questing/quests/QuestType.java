package me.vrekt.oasis.questing.quests;

import me.vrekt.oasis.questing.Quest;
import me.vrekt.oasis.questing.quests.tutorial.ANewHorizonQuest;

/**
 * All quests
 */
public enum QuestType {

    A_NEW_HORIZON {
        @Override
        public Quest create() {
            return new ANewHorizonQuest();
        }
    },

    SPORES_OF_THE_GROVE {
        @Override
        public Quest create() {
            return new me.vrekt.oasis.questing.quests.mycelia.SporesOfTheGroveQuest();
        }
    };

    public abstract Quest create();
}
