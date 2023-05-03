import time
import random
import pyautogui
import utilities.api.item_ids as ids
import utilities.color as clr
import utilities.random_util as rd
import utilities.imagesearch as imsearch
from model.osrs.osrs_bot import OSRSBot
from utilities.api.morg_http_client import MorgHTTPSocket
from utilities.api.status_socket import StatusSocket

class OSRSAltar(OSRSBot):

    def __init__(self):
        bot_title = "ZMI Altar runner"
        description = "Runs to the ourania Altar. Required 85 runecrafting already."
        super().__init__(bot_title=bot_title, description=description)
        # Set option variables below (initial value is only used during UI-less testing)
        self.running_time = 1
        self.invetory_open = False
        self.api_m = MorgHTTPSocket()
        self.api_s = StatusSocket()
        
        

    def create_options(self):
        self.options_builder.add_dropdown_option("pouch","Use pouch?",["no","colossal_pouch"])
        self.options_builder.add_slider_option("running_time", "How long to run (minutes)?", 1, 300)
        self.options_builder.add_slider_option("min_run_energy", "When to drink stamina potion", 1, 100)

    def save_options(self, options: dict):
        for option in options:

            if option == "running_time":
                self.running_time = options[option]

            elif option == "pouch":
                self.pouch = options[option]

            elif option == "min_run_energy":
                self.min_run_energy = options[option]
                
            else:
                self.log_msg(f"Unknown option: {option}")
                print("Developer: ensure that the option keys are correct, and that options are being unpacked correctly.")
                self.options_set = False
                return
            
        self.log_msg(f"Running time: {self.running_time} minutes.")
        self.log_msg("Using pouch(es): " + self.pouch)
        self.log_msg("Options set successfully.")
        self.options_set = True

    def main_loop(self):

        # Set rounds to 0 when starting bot
        self.round_since = 0

        # Save starting XP
        self.starting_xp = self.api_m.get_skill_xp(skill="Runecraft")

        # Main loop
        start_time = time.time()
        end_time = self.running_time * 60

        # Set a variable to store total runs
        i = 0
     
        while time.time() - start_time < end_time:
            # -- Perform bot actions here --
            # Code within this block will LOOP until the bot is stopped.

            # Inform how many runs we did
            str_msg = "Runs: " + str(i)
            self.log_msg(str_msg)

            str_msg = "Runs since last repair: " + str(self.round_since)
            self.log_msg(str_msg)

            str_msg = "XP Gained: " + str( self.api_m.get_skill_xp(skill="Runecraft") - self.starting_xp )
            self.log_msg(str_msg)

            # If we are outside, start ladder sequence
            if self.api_m.get_player_region_data()[2] == 9778:
                self.log_msg("Starting click_ladder")
                if not self.click_ladder():
                    self.log_msg("Aborted click_ladder")
                    break
            
            # If we are inside, start bank sequence
            if self.api_m.get_player_region_data()[2] == 12119:
                self.log_msg("Starting handle_banking")
                if not self.handle_banking():
                    self.log_msg("Aborted handle_banking")
                    break

            time.sleep(1)
            self.log_msg("Starting handle_altar")
            if not self.handle_altar():
                self.log_msg("Aborted handle_altar")
                break

            if self.round_since > 3 and not self.pouch == "no":
                if self.api_m.get_if_item_in_inv(ids.COSMIC_RUNE):
                    if self.maybe_click_npc_talk():
                        self.round_since = 0
            self.round_since = self.round_since + 1 
       
            i = i + 1
            self.update_progress((time.time() - start_time) / end_time)

        self.update_progress(1)
        str_msg = "XP Gained: " + str( self.api_m.get_skill_xp(skill="Runecraft") - self.starting_xp )
        self.log_msg(str_msg)
        self.log_msg("Finished.")
        self.logout_runelite()
        self.stop()

    def handle_banking(self):

        # Handles the open and deposit squence
        self.log_msg("Start open_and_deposit")
        if not self.open_and_deposit():
            return False
        
        # Handles the drinking of potion sequence
        self.log_msg("Start maybe_drink_potion")
        if not self.maybe_drink_potion():
            return False
        
        # Handles getting items from the bank
        self.log_msg("Start get_items_and_close")
        if not self.get_items_and_close():
            return False
        
        # Return True if all passess
        return True
            
    def handle_altar(self):
        loop = True
        first = True

        while loop:
            # First time clicking altar with set parameter
            if first:
                self.click_altar(True)
                first = False

                # If no pouched used, break the loop.
                if self.pouch == "no":
                    break

                continue

            # If inv contains pure essence, click_altar
            if self.api_m.get_if_item_in_inv(ids.PURE_ESSENCE):
                # self.log_msg('inv contains essence, clicking altar')
                self.click_altar()
            else:
                # self.log_msg('Clicking colossol pouch')
                self.click_colossal_pouch(True)
                if len(self.api_s.get_inv()) == 28:
                    continue


                if len(self.api_s.get_inv()) != 28:
                    if self.api_m.get_if_item_in_inv(ids.PURE_ESSENCE):
                        self.click_altar()
                    break
                    
        self.click_teleport()
        return True
    
    def maybe_click_npc_talk(self):
        if self.api_m.get_if_item_in_inv(ids.COSMIC_RUNE):

            self.log_msg("Repairing pouch sequence started")
            # Click the spellbook tab
            # self.mouse.move_to(self.win.cp_tabs[6].random_point(), mouseSpeed="fastest")
            # self.mouse.click()
            #self.log_msg("Opened spellbook")
            tries = 0
            time.sleep(2/10)
            while True:
                npc_contact_img = imsearch.BOT_IMAGES.joinpath("spellbooks", "lunar", "NPC_Contact.png")
                
                if npc_contact := imsearch.search_img_in_rect(npc_contact_img, self.win.control_panel):
                    #self.log_msg("NPC contact found, right clicking")
                    # Move to a random point
                    self.mouse.move_to(npc_contact.random_point())
                    self.mouse.right_click()
                    time.sleep(6/10)

                    dark_mage_img = "C:\\Users\\rober\\Documents\\OSRS-Bot-COLOR-main\\OSRS-Bot-COLOR-main\\src\\images\\bot\\mouse_clicks\\dark_mage.png"
                    
                    dark_mage  = pyautogui.locateOnScreen(dark_mage_img,confidence=0.8)
                    dark_mage_tries = 0
                    dark_mage_mage_failed = False
                    while not dark_mage:
                        
                        dark_mage  = pyautogui.locateOnScreen(dark_mage_img,confidence=0.8)
                        if dark_mage:
                            break
                        time.sleep(2/10)
                        if dark_mage_tries == 20:
                            self.log_msg("failed")
                            dark_mage_mage_failed = True
                            break 
                        dark_mage_tries = dark_mage_tries + 1
                        self.log_msg(dark_mage_tries)
                    if dark_mage_mage_failed:
                        continue
                    point = self.random_point(dark_mage.left, dark_mage.top, dark_mage.width, dark_mage.height)
                    
                    self.mouse.move_to( destination=(point[0],point[1]))
                    self.mouse.click()

                    self.do_dialogue()
                    break
                tries = tries + 1
                time.sleep(10)
                if tries > 3:
                    return False
        return True
    
    def random_point(self, left, top, width, height):
        x = random.randint(left, left+width)
        y = random.randint(top, top+height)
        return (x, y)

    def do_dialogue(self):
        
        time.sleep(3)

        dialogue_1_img = imsearch.BOT_IMAGES.joinpath("mouse_clicks", "dialogue_1.png")
        dialogue_1 = imsearch.search_img_in_rect(dialogue_1_img, self.win.chat,confidence=0.01)
        while not dialogue_1:
            time.sleep(1/2)
            dialogue_1 = imsearch.search_img_in_rect(dialogue_1_img, self.win.chat,confidence=0.01)
        self.log_msg("Dialogue 1 detected. [Space]")
        pyautogui.press('space')
        time.sleep(6/10)
        
        dialogue_2_img = imsearch.BOT_IMAGES.joinpath("mouse_clicks", "dialogue_2.png")
        dialogue_2 = imsearch.search_img_in_rect(dialogue_2_img, self.win.chat,confidence=0.01)
        while not dialogue_2:
            time.sleep(1/2)
            dialogue_2 = imsearch.search_img_in_rect(dialogue_2_img, self.win.chat,confidence=0.01)
        self.log_msg("Dialogue 2 detected. [2]")
        pyautogui.press('2')
        time.sleep(6/10)
        
        dialogue_3_img = imsearch.BOT_IMAGES.joinpath("mouse_clicks", "dialogue_3.png")
        dialogue_3 = imsearch.search_img_in_rect(dialogue_3_img, self.win.chat,confidence=0.01)
        while not dialogue_3:
            time.sleep(1/2)  
            dialogue_3 = imsearch.search_img_in_rect(dialogue_3_img, self.win.chat,confidence=0.01)
        self.log_msg("Dialogue 3 detected. [Space]")
        pyautogui.press('space')
        time.sleep(6/10)
        
        dialogue_4_img = imsearch.BOT_IMAGES.joinpath("mouse_clicks", "dialogue_4.png")
        dialogue_4 = imsearch.search_img_in_rect(dialogue_4_img, self.win.chat,confidence=0.01)
        while not dialogue_4:
            time.sleep(1/2)
            dialogue_4 = imsearch.search_img_in_rect(dialogue_4_img, self.win.chat,confidence=0.01)
        self.log_msg("Dialogue 4 detected. Continueing")
        return True
        

    def click_teleport(self):
        #self.log_msg("Open spellbook")
        self.mouse.move_to(self.win.cp_tabs[6].random_point(), mouseSpeed="fastest")
        self.mouse.click()
        self.invetory_open = False

        ourania_teleport_img = imsearch.BOT_IMAGES.joinpath("spellbooks", "lunar", "Ourania_Teleport.png")

        time.sleep(2/10)
        ourania_teleport = imsearch.search_img_in_rect(ourania_teleport_img, self.win.control_panel)
        while not ourania_teleport:
            ourania_teleport = imsearch.search_img_in_rect(ourania_teleport_img, self.win.control_panel)
            time.sleep(2/10)

        # Move to a random point
        self.mouse.move_to(ourania_teleport.random_point())
        #self.log_msg("Move to teleport")
        # Set tries to 0
        tries = 0

        # While Fill is not in text, move mouse.
        while not self.mouseover_text(contains="Ouran"):
            # Stop after 5 tries
            
            self.mouse.move_to(ourania_teleport.random_point())
            time.sleep(2/10)

            if tries > 5:           
                self.log_msg('Failed to find Ouran')
                break

        # the actual click
        self.mouse.click()
        #self.log_msg("Click teleport")
        tries = 0
        lantern = self.get_nearest_tag(clr.BLUE)
        while not lantern:
            time.sleep(2/10)
            lantern = self.get_nearest_tag(clr.BLUE)
            tries = tries + 1
            if tries == 18:
                # the actual click
                self.mouse.move_to(ourania_teleport.random_point())
                self.mouse.click()
            if tries == 36:
                return False
        
        #self.log_msg("Locatation changed")
        return True





    def get_items_and_close(self):
        
        # Click pure essence once
        if not self.click_pure_essence():
            return False
        if self.pouch == "colossal_pouch":
            # Click pouch
            if not self.click_colossal_pouch(False, "Fill"):
                return False
            
            # Click pure essence once
            if not self.click_pure_essence():
                return False
            
            # Click pouch
            if not self.click_colossal_pouch(False, "Fill"):
                return False
            
            # Click pure essence once
            if not self.click_pure_essence():
                return False
        
        # Success
        pyautogui.press('esc')  
        return True
      

    def click_pure_essence(self, inventory_change = False):
         # Get the image path of the pouch
        pure_essence_img = imsearch.BOT_IMAGES.joinpath("items", "Pure_essence.png")

        if inventory_change:
            # Save current inv quantity
            current_inv_qt = len(self.api_s.get_inv())
            time.sleep(6/10)
            new_inv = current_inv_qt
            self.log_msg('Waiting for inventory change: True')

        # Is colossal pouch even in view? 
        if pure_essence := imsearch.search_img_in_rect(pure_essence_img, self.win.game_view,confidence=0.05):

            # Move to a random point
            self.mouse.move_to(pure_essence.random_point())

            # Set tries to 0
            tries = 0

            # While Fill is not in text, move mouse.
            while not self.mouseover_text(contains="Pure"):
                # Stop after 5 tries
                
                self.mouse.move_to(pure_essence.random_point())
                time.sleep(2/10)

                if tries > 5:
                    
                    self.log_msg('Failed to find Pure')
                    return False
            
            # the actual click
            self.mouse.click()

            # If inventory change is true, execute while loop waiting for inventory change
            if inventory_change:
                while current_inv_qt == new_inv:
                    if tries > 5:
                        self.log_msg('No inventory change detected')
                        return False
                    time.sleep(4/10)
                    tries = tries + 1
                    new_inv = len(self.api_s.get_inv())
            
            # completed click successfull
            # self.log_msg('Clicked Pure essence')
            return True
        

        else:
            # No pouch found on screen
            self.log_msg('No essence found, are you sure those are in the bank?')
            return False


    # Function to click on colossal pouch
    def click_colossal_pouch(self, inventory_change = False, empty_fill = "Empty"):
        # Get the image path of the pouch
        colossal_pouch_img = imsearch.BOT_IMAGES.joinpath("items", "Colossal_pouch.png")

        if inventory_change:
            # Save current inv quantity
            current_inv_qt = len(self.api_s.get_inv())
            time.sleep(6/10)
            new_inv = current_inv_qt
            self.log_msg('Waiting for inventory change: True')

        # Is colossal pouch even in view? 
        if colossal_pouch := imsearch.search_img_in_rect(colossal_pouch_img, self.win.control_panel):

            # Move to a random point
            self.mouse.move_to(colossal_pouch.random_point())

            # Set tries to 0
            tries = 0

            # While Fill is not in text, move mouse.
            while not self.mouseover_text(contains=empty_fill):
                # Stop after 5 tries
                
                self.mouse.move_to(colossal_pouch.random_point())
                time.sleep(2/10)
                tries = tries + 1
                if empty_fill == "Fill" and self.mouseover_text(contains="Depo"):
                    return True
                if tries > 5:
                    
                    self.log_msg('Failed to find '+empty_fill)
                    return False
            
            # the actual click
            self.mouse.click()
            
            # If inventory change is true, execute while loop waiting for inventory change
            if inventory_change:
                while current_inv_qt == new_inv:
                    if tries > 16:
                        self.log_msg('No inventory change detected')
                        return False
                    time.sleep(1/10)
                    tries = tries + 1
                    new_inv = len(self.api_s.get_inv())
   
            # completed click successfull
            # self.log_msg('Clicked colossal pouch')
            return True
        

        else:
            # No pouch found on screen
            self.log_msg('No pouch found on screen')
            return False
    
    def maybe_drink_potion(self):

        if self.get_run_energy() < self.min_run_energy:
            stamina_potion1_img = imsearch.BOT_IMAGES.joinpath("items", "stamina_potion1.png")
            if stamina_potion1 := imsearch.search_img_in_rect(stamina_potion1_img, self.win.game_view):
                # Found image
                # self.log_msg('Move to potion')
                self.mouse.move_to(stamina_potion1.random_point())
            else:
                self.log_msg('Failed to find stamina potions')
                return False
            
            # Save current inv quantity
            current_inv_qt = len(self.api_s.get_inv())
            self.mouse.click()
            tries = 0
            while current_inv_qt == len(self.api_s.get_inv()):
                if tries > 5:
                    self.log_msg('Failed to continue, stopping')
                    return False
                time.sleep(6/10)
                tries = tries + 1

            if stamina_potion1 := imsearch.search_img_in_rect(stamina_potion1_img, self.win.control_panel):
                   # Found image
                # self.log_msg('Move to potion')
                self.mouse.move_to(stamina_potion1.random_point())
            else:
                self.log_msg('Failed to find stamina potions')
                return False
            
            # Save current inv quantity
            current_inv_qt = len(self.api_s.get_inv())
            self.mouse.click()

            while current_inv_qt == len(self.api_s.get_inv()):
                if tries > 5:
                    self.log_msg('Failed to continue, stopping')
                    return False
                time.sleep(6/10)
                tries = tries + 1
            return True
        return True
                
                


    def open_and_deposit(self):
        # Get the path to the image
        deposit_all_img = imsearch.BOT_IMAGES.joinpath("bank", "deposit_all.png")

        banker = self.get_nearest_tag(clr.CYAN)
        tries = 0
        while not banker:
            time.sleep(2/10)
            banker = self.get_nearest_tag(clr.CYAN)
            tries = tries + 1
            if tries > 20:
                self.log_msg('Could not locate banker')
                return False
            
        # Find banker
        if banker:
           
            # Set a var for keeping the while loop running
            bank_not_opened = True
            tries = 0

            # Run until bank is opened.
            while bank_not_opened:

                # Stop after 5 tries
                if tries > 5:
                    self.log_msg('Failed to continue, stopping')
                    return False
                
                self.mouse.move_to(banker.random_point())

                # Does text match Bank?
                if not self.mouseover_text(contains="Bank"):
                    # If not, start the ladder cyclus again
                    self.log_msg('Could not locate bank, trying again')
                    banker = self.get_nearest_tag(clr.CYAN)
                    time.sleep(3/10)
                    tries = tries + 1
                    continue
                # self.log_msg("Found banker")
                # Found climb, clicking ladder
                self.mouse.click()
                # self.log_msg('click on banker, waiting...')

                # Sleep for 1 second
                deposit_all = imsearch.search_img_in_rect(deposit_all_img, self.win.game_view)
                # Waiting till player is idle
                while not deposit_all:
                    deposit_all = imsearch.search_img_in_rect(deposit_all_img, self.win.game_view)
                    time.sleep(3/10)
                self.log_msg("bank opened")
                if len(self.api_s.get_inv()) > 2:
                    
                    # self.log_msg("Bank opened")
                    # While Deposit is not in text, move mouse.
                    while not self.mouseover_text(contains="inventory"):
                        # Stop after 5 tries
                        if tries > 5:
                            self.log_msg('Failed to continue, stopping')
                            return False
                        
                    
                        if deposit_all := imsearch.search_img_in_rect(deposit_all_img, self.win.game_view):
                            # Found image
                            # self.log_msg('Move to deposit button')
                            self.mouse.move_to(deposit_all.random_point())
                        else:
                            self.log_msg('Failed to find deposit all')
                            tries = tries + 1
                            continue
                    
                    
                    # Save current inv quantity
                    current_inv_qt = len(self.api_s.get_inv())

                    # Click to deposit
                    # self.log_msg('Clicked deposit')
                    self.mouse.click()

                    time.sleep(6/10)

                    while current_inv_qt == len(self.api_s.get_inv()):
                        if tries > 5:
                            self.log_msg('Failed to continue, stopping')
                            return False
                        time.sleep(6/10)
                        tries = tries + 1

                    # self.log_msg('Deposited items')
                return True
                


                
            

    def click_altar(self, first = False):

    
        tries = 0
        toggle_run = False
        # Find 
        if altar := self.get_nearest_tag(clr.PINK):
            altar_not_found = True
            while altar_not_found:

                self.mouse.move_to(altar.random_point())
                # if not self.mouseover_text(contains="Craft"):
                #     continue
                if first:
                    self.mouse.right_click()
                    time.sleep(3/10)

                    craft_runes_img = imsearch.BOT_IMAGES.joinpath("mouse_clicks", "craft_rune.png")
                    craft_runes = imsearch.search_img_in_rect(craft_runes_img, self.win.game_view)

                    while not craft_runes:
                        craft_runes = imsearch.search_img_in_rect(craft_runes_img, self.win.game_view)
                        time.sleep(3/10)
                        
                    self.mouse.move_to(craft_runes.random_point())
                
                self.mouse.click()
                
               
                altar_not_found = False
                # self.log_msg('click on altar, waiting')
            
            if first:
                time.sleep(3)
            
            current_inv_qt = len(self.api_s.get_inv())
          
            while current_inv_qt == len(self.api_s.get_inv()):
                
                

                if first:
                    if not self.invetory_open:
                        if rd.random_chance(probability=0.01):
                            # Click the inventory tab
                            self.mouse.move_to(self.win.cp_tabs[3].random_point())
                            self.mouse.click()
                            self.invetory_open = True
                    if not toggle_run:
                        self.toggle_run(toggle_on=True)
                        toggle_run = True 
                    if tries > 300:
                        self.log_msg('Failed to complete lap')
                        return False
                else:
                    if tries > 25:
                        self.log_msg('Failed to complete lap')
                        return False
                time.sleep(1/10)
                tries = tries + 1

            if first:
                if not self.invetory_open:
                    self.mouse.move_to(self.win.cp_tabs[3].random_point())
                    self.mouse.click()
                    self.invetory_open = True
            return True
        return False

    def click_ladder(self):

        
        # Start with try 0
        tries = 0

        # Save current location ID for later
        location_id = self.api_m.get_player_region_data()[2]

        ladder = self.get_nearest_tag(clr.BLUE)
        # Find ladder        
        while not ladder:
            self.set_compass_south()
            self.move_camera(0,-30)
            
            self.log_msg('Cant find ladder, ajusting camera')
            time.sleep(3/10)
            ladder = self.get_nearest_tag(clr.BLUE)
            tries = tries + 1
            if tries > 5:
                return False

        # Set the var of ladder not found/clicked to True
        ladder_not_found = True

        # While ladder is not clicked loop
        while ladder_not_found:

            if tries > 5:
                self.log_msg('Failed to continue, stopping')
                return False
            
            # Moving mouse to ladder
            # self.log_msg('Move mouse to ladder')
            self.mouse.move_to(ladder.random_point())
            self.mouse.right_click()
            time.sleep(3/10)

            climb_ladder_img = imsearch.BOT_IMAGES.joinpath("mouse_clicks", "climb_ladder.png")
            climb_ladder = imsearch.search_img_in_rect(climb_ladder_img, self.win.game_view)

            while not climb_ladder:
                
                time.sleep(3/10)
                climb_ladder = imsearch.search_img_in_rect(climb_ladder_img, self.win.game_view)
                tries = tries + 1
                
            self.mouse.move_to(climb_ladder.random_point())

            
            # Found climb, clicking ladder
            self.mouse.click()
            # self.log_msg('click on ladder, waiting till we reach dungeon')

            # Sleep for 1 second
            time.sleep(1)
            

            # Waiting till player is idle
            while not self.api_m.get_is_player_idle():
                time.sleep(3/10)
                if not self.invetory_open:
                    if rd.random_chance(probability=0.06):
                        # Click the inventory tab
                        self.mouse.move_to(self.win.cp_tabs[3].random_point())
                        self.mouse.click()
                        self.invetory_open = True
                bank = self.get_nearest_tag(clr.CYAN)
                if bank:
                    return True

            # Check if we changed region
            if location_id != self.api_m.get_player_region_data()[2]:
                # Return True if region changed
                return True
            else:
                # Region did not change, something went wrong, try again
                self.log_msg('Region did not change')
                tries = tries + 1
                continue

        # self.log_msg('[Failed] Failed to find ladder')
        # return False

