SparkFun Charm High Desktop Pick and Place
========================================

![SparkFun Low Cost Desktop Pick and Place Machine](https://cdn.sparkfun.com/assets/home_page_posts/2/5/8/6/Pick-Place-Setup-1.jpg)

The CHMT36VA is a $2800 desktop sized pick and place machine from Charm High. We use it to produce a variety of designs, 50 to 100pcs at a shot. It works very well for low-volume high-mix pick and place of 0603 based designs.

The main purposed of this repo is the [Eagle Conversion ULP](https://github.com/sparkfunX/Desktop-PickAndPlace-CHMT36VA/tree/master/Eagle-Conversion) and the English Language file. The Conversion ULP offers the user a GUI that looks like this:

![Conversion GUI](https://github.com/sparkfunX/Desktop-PickAndPlace-CHMT36VA/raw/master/Conversion%20GUI.jpg)

This allows the user to take in an Eagle BRD file and output the recipe file that the CHMT36VA expects. This cuts down on setup time of the machine dramatically.

The [English Language conversion file](https://github.com/sparkfunX/Desktop-PickAndPlace-CHMT36VA/tree/master/Language-File) is our translation and typo fixes of the Charm High provided english file.

Do you have one of these machines? Want to share your tips and tricks and ask other owners a question? Join the [Desktop Pick and Place google group](https://groups.google.com/d/forum/desktop-pick-and-place)!

Be sure to checkout our posts on the machine:

* [Unboxing](https://www.sparkfun.com/sparkx/blog/2586)
* [Leader Cheaters](https://www.sparkfun.com/sparkx/blog/2588)
* [Installing the Charm High Software](https://www.sparkfun.com/sparkx/blog/2594)
* [A better English translation](https://www.sparkfun.com/sparkx/blog/2595)
* [An EAGLE ULP](https://www.sparkfun.com/sparkx/blog/2591) to setup new jobs on the machine quickly

Repository Contents
-------------------

* **/Eagle-Conversion** - Takes an EAGLE design and outputs a work file complete with feeder data. See [SparkFun Charm EAGLE Conversion ULP](https://www.sparkfun.com/sparkx/blog/2591) for more information.
* **/KiCad-Conversion** - Same as EAGLE but less developed. It works, but less bells and whistles.
* **/Language-File** - A new smt_English.qm file for easier to understand error messages and buttons
* **/Software** - The various versions of the Windows based Charm High software
* **/User-Manuals** - Various manuals from different machines in an attempt to piece together various poorly translated or documented features

Related Projects
----------------

* [PNPConvert](https://github.com/hydra/pnpconvert) Conversion utility with DipTrace support, written in Groovy.

License Information
-------------------

This product is _**open source**_! 

Please review the LICENSE.md file for license information. 

If you have any questions or concerns on licensing, please contact techsupport@sparkfun.com.

Please use, reuse, and modify these files as you see fit. Please maintain attribution to SparkFun Electronics and release any derivative under the same license.

Distributed as-is; no warranty is given.

- Your friends at SparkFun.
