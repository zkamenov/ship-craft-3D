# ShipCraft 3D

This is a 3D Minecraft-style game where one can explore an infinite world, and
remove and place blocks throughout 3 different worlds: Earth, the Moon, and Venus. Pretty much anything can be created out of the blocks, and worlds
can be saved. This is written in Python 3.

## How to Run

To run the program, go into the terminal at the location of this folder and type
|./build.sh|, which compiles the Cython functions and runs the main program.

If a permission error occurs, type |chmod +x build.sh|, which grants the user
permission to execute the shell script. Then try ./build.sh
If issues persist, type in the following into the terminal:

```
python setup.py build_ext --inplace
python Main.py
```

### Controls

`w` - move forward

`a` - move leftward

`s` - move backward

`d` - move rightward

`<space>` - jump

`i` - switch dimensions

`e` - access inventory

`<click>` - mine (hand is empty) / place (block in hand) / switch items (inventory)

`<digit>` - select item in hotbar

`r` - shift map

`k` - save to slot

`l` - load slot

`o` - decrease screen resolution (useful for speed)

`p` - increase screen resolution (useful for screenshots)

`n` - decrease max render distance

`m` - increase max render distance

If you would like to re-access the castle save, go to the save folder and copy
the contents of the Castle folder and paste them into the w0 folder

## Known Bugs

If you are on a Mac, the accent menu will mess with the way key releases are
listened for. To stop this, disable key repeats, or disable accent menu by
executing the following command in the terminal:

`defaults write -g ApplePressAndHoldEnabled -bool false`

To re-enable accent menu, execute this command:

`defaults write -g ApplePressAndHoldEnabled -bool true`

[Source of Fix](https://superuser.com/questions/1257641/disable-mac-typing-accent-menu#:~:text=1%20Answer&text=is%20not%20useful,Show%20activity%20on%20this%20post.,them%20to%20load%20the%20setting.)

