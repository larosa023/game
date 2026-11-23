## Fix: the game closed right after the splash screen
The Windows version came with a cut-down copy of Java that was missing the part the updater uses to check for new versions, so the game crashed when the main menu opened. That part is now included.

- Every build now runs the packaged game's Java against all of the game's code on a Windows machine before it's released, so this kind of crash can't ship again.
- If the game ever does crash, it now writes a `crash.log` to `%APPDATA%\Oasis` that you can send over.
- The update check can no longer stop the game from starting, even if it fails.

**Coming from v1.0.6 or older:** download this version manually one more time, because the older versions crash before the update button appears. After this, updates work from the main menu.
