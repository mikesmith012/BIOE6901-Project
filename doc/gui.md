# GUI Module

Author: Mike Smith

Date of Implementation: 16/04/2023

## Description:

Sets the layout of the graphical user interface. Does not handle any logic or user inputs. Only provides variables that reference respective on-screen elements. 

This module is auto-generated from the "ui/gui.ui" file. The following command can be used to generate this module:

`pyuic5 -x ui/gui.ui -o gui.py`

## Module methods:

`def setupUi(self, MainWindow)`
- Sets up the layout of the graphical user interface.

`def retranslateUi(self, MainWindow)`
- Set up defaults for the user interface elements. Eg: Sets up default text for all labels and action menu elements.