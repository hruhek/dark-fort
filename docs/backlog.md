# wandering the dungeon
- [ ] player will be able to wander around the dungeon choosing what door to go through in each room

# random encounter when returning to explored room
- [ ] when coming back to explored room, run random encounter (1-in-4 chance of Weak monster per DARK_FORT rules)

# exit dungeon from entrance room
- [ ] ENTRANCE ROOM should have "Exit Dungeon" option
- [ ] to leave dungeon and level up, player needs to return to ENTRANCE ROOM
- [ ] if user has enough gold when he exits dungeon add option to give gold away for level up

# exit the dungeon for level up
- [ ] when player has enough points (15) and explored rooms (12), add message to exit dungeon and level up in ENTRANCE ROOM

# leveling up
- [ ] check that each level up option can be used only one
- [ ] apply level up benefits to player character
- [ ] when player has enough points, or explored rooms, it should stop accumulating them until the player leaves the dungeon and levels up

# save/load
- [ ] add save/load game feature

# shop selling & limited stock
- [ ] enable selling of items in shop for half price
- [ ] shop will have limited stock for each item
- [ ] shop stock will reset for each new encounter

# dungeon generation
- [ ] dungeon will need to be generated on start of the game
- [ ] after the player exits the first dungeon, the second dungeon should be generated
- [ ] if there are multiple dungeons, player should have option to choose which one to enter
- [ ] each dungeon should have unique name
- [ ] if dungeon has all rooms explored, it should have explored added to it's name
- [ ] generated dungeons and exploration progress should be included in save game
- [ ] load game should restore dungeons and each dungeon exploration progress

# entrance room
- [ ] ENTRANCE room should also have exits generated and displayed before initial encounter
- [ ] dungeon exit should also be present, even if player is not ready for level up
- [ ] dungeon exit can be used if dungeon is too small for player to gather enough points or explored rooms to level up, so player can go to the next dungeon

# combat
- [ ] some monsters have special attack that kill player (ex. medusa gaze). when that happens players should get to 0 HP and die

# unified exit button/shortcut
- [ ] leaving inventory screen or shop should have same shortcut/button

# dungeon map display
- [ ] show a 2D map of the dungeon with rooms placed on a grid based on exit directions