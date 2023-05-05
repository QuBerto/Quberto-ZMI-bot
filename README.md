
# ZMI Altar OSBC bot 

ZMI altar bot to craft runes at the ZMI altar. This is the first bot i made in OSBC. Basicly does the following


## Bot features

- Handles banking and filling of pouches.
- Drinks stamina potion(1) if run energy is low.
- Craft runes at altar, both from inventory and from pouches.
- Uses ourania teleport.
- Repairs pouch (Currently only colossal pouch, every 4th run unless no cosmic rune in inventory).
- Runs back to bank.


## How to setup

1. Copy altar.py to src\model\
2. Place directory with images "altar_bot" in src\images\bot
3. Add the following line to src\model\\\_\_init__.py
```python
  from .altar import OSRSAltar
```
4. Setup plugins





## Plugins  used

* Entity hider\
    ![117HD](https://i.imgur.com/Q10wNIc.png)
* Object markers
    * Be sure to read the section object markers on what objects to mark
* 117 HD (Plugin hub)
    * set Draw distance to max (90)
    * (optional) set all settings to lowest/off to minimize cpu/memory usage\
    ![117HD](https://i.imgur.com/Ki9Hp3T.png)
* Status socket (Plugin hub)
* Morg HTTP client (Plugin hub)
* Runecrafting utilities (Plugin hub)\
    ![117HD](https://i.imgur.com/e6ZwvUY.png)
## Object/NPC markers
1. Mark the ladder outside with Blue
![117HD](https://i.imgur.com/DWWcJQp.png)
2. Mark the banker inside with Blue
![117HD](https://i.imgur.com/bymzwpJ.png)
3. Mark the altar Purple
![117HD](https://i.imgur.com/bwmJB58.png)

## How to setup bank/inventory
Each time you want to bank, the banker asks 20 runes of the same type. You can setup a what type of rune is used for banking by talking to the banker. This has to be set for the bot to function. I suggest picking mind runes since these are cheap.\
\
Grab your runepouch from the bank and the runes you want to bring. I suggest putting law/astral/mind runes in your runepouch. Remove runepouch placeholder from the banker.\
\
If you are using a colossal pouch. Remove that placeholder as well.

1. Fill your bank with placeholders
2. Stamina potions(1) in view, closer to inventory is better.
3. Pure essence in view, closer to inventory is better.
4. Set quantity to "All"
![117HD](https://i.imgur.com/yHuKweo.png)