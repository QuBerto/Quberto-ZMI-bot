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
        bot_title = "ZMI Altar Bot"
        description = "Runs to the ourania Altar. Supports colossal pouch or no pouches."
        super().__init__(bot_title=bot_title, description=description)
        self.running_time = 1
        self.invetory_open = False
        self.api_m = MorgHTTPSocket()

        
    def create_options(self):
        self.options_builder.add_slider_option("running_time", "How long to run (minutes)?", 1, 360)
        self.options_builder.add_slider_option("min_run_energy", "When to drink stamina potion", 1, 100)
        self.options_builder.add_slider_option("panic_stop", "Low health threshold", 1, 99)
        self.options_builder.add_dropdown_option("eat_food", "Eat lobsters when low health?", ["NONE","LOBSTER","SHARK"])      
        self.options_builder.add_checkbox_option("pouch","Use pouch?",["Small_pouch","Medium_pouch","Large_pouch","Giant_pouch","Colossal_pouch"])
        self.options_builder.add_slider_option("repair_after", "After how many rounds, pouches should be repaired?", 1, 20)
        self.options_builder.add_checkbox_option("repair_now", "Repair first round?", ["on"])  
        self.options_builder.add_checkbox_option("insane_mode", "Turn fast mode on?", ["on"])   
        self.options_builder.add_checkbox_option("debug_on", "Turn debug log on?", ["on"])    

    def save_options(self, options: dict):
        self.debug_on = False
        self.repair_now = False
        self.insane_mode = False
        self.eat_food = False
        self.mouse_speed = "fast"

        for option in options:
            if option == "running_time":
                self.running_time = options[option]
            elif option == "pouch":
                if "Colossal_pouch" in options[option]:
                    if not self.is_only_value_in_list(options[option],"Colossal_pouch"):
                        self.log_msg("Cant choose colossal pouch with any other pouch.")
                        self.options_set = False
                        return
                self.pouch = options[option]
            elif option == "min_run_energy":
                self.min_run_energy = options[option]        
            elif option == "panic_stop":
                self.panic_stop = options[option] 
            elif option == "repair_after":
                self.repair_after = options[option] 
            elif option == "repair_now":
                if "on" in options[option]:
                    self.repair_now = True
            elif option == "debug_on":
                if "on" in options[option]:
                    self.debug_on = True
            elif option == "insane_mode":
                if "on" in options[option]:
                    self.mouse_speed = "fastest"
                    self.insane_mode = True
            elif option == "eat_food":
                if "NONE" in options[option]:
                    self.eat_food = False
                else:
                    
                    type_food = getattr(ids, options[option])
                    if type_food:
                        self.eat_food = True
                        self.type_food = options[option]
                        self.type_food_id = type_food
                
            else:
                self.log_msg(f"Unknown option: {option}")
                print("Developer: ensure that the option keys are correct, and that options are being unpacked correctly.")
                self.options_set = False
                return
        separator = ", "
        result = separator.join(self.pouch)

        self.log_msg(f"Running time: {self.running_time} minutes.")
        self.log_msg("Using pouch(es): " + result)
        self.log_msg("Drink potion below: " + str(self.min_run_energy) + "%")
        self.log_msg("Options set successfully.")
        if self.debug_on:
            self.log_msg("Debug is on.")

        self.options_set = True

    def is_only_value_in_list(self, lst, value):
        """
        Returns True if the given value is the only element in the list,
        and False otherwise.
        """
        if len(lst) == 1 and lst[0] == value:
            return True
        else:
            return False
        
    def debug(self, msg):
        if self.debug_on:
            self.log_msg(msg)

    def main_loop(self):
        if not self.start_loop_function():
            self.log_msg("Finished.")
            self.logout_runelite()
            self.stop()

        i = 0
        start_time = time.time()
        end_time = self.running_time * 60

        while time.time() - start_time < end_time:
            
            str_msg = "Runs: " + str(i) + " (Last repair: "+ str(self.round_since)+" ago)"
            self.log_msg(str_msg )

            xp_gained = self.api_m.get_skill_xp(skill="Runecraft") - self.starting_xp

            str_msg = "XP Gained: " + str( xp_gained )
            self.log_msg(str_msg)
            

            # Outside
            if self.api_m.get_player_region_data()[2] == 9778:
                self.debug("Starting click_ladder")
                if not self.click_ladder():
                    self.log_msg("Aborted click_ladder")
                    break
            
            # Bank area
            if self.api_m.get_player_region_data()[2] == 12119:
                self.debug("Starting handle_banking")
                if not self.handle_banking():
                    self.log_msg("Aborted handle_banking")
                    break

            self.debug("Starting handle_altar")
            if not self.handle_altar():
                self.log_msg("Aborted handle_altar")
            self.click_teleport()

            if self.round_since > self.repair_after and not self.pouch == "no" or self.repair_now == True:
                if self.api_m.get_if_item_in_inv(ids.COSMIC_RUNE):
                    if self.maybe_click_npc_talk():
                        self.round_since = 0
                        self.repair_now = False

            self.round_since = self.round_since + 1 
            i = i + 1
            self.update_progress((time.time() - start_time) / end_time)

            self.log_msg(str(13030000 - self.api_m.get_skill_xp(skill="Runecraft"))+ " Till stopping") 

          

        self.update_progress(1)
        str_msg = "XP Gained: " + str( self.api_m.get_skill_xp(skill="Runecraft") - self.starting_xp )
        self.log_msg(str_msg)
        self.log_msg("Finished.")
        self.logout()
        self.stop()

    def start_loop_function(self):
        self.round_since = 0
        self.starting_xp = self.api_m.get_skill_xp(skill="Runecraft")
        self.deposit_rectangle = False
        self.pouch_position = False
        self.bank_position_essence = False
        self.last_banker = False

        self.set_compass_south()
        self.open_inventory()
        if not self.set_pouch_position():
            return False
        
        pyautogui.scroll(-50)
        return True

    def set_pouch_position(self):
        dict_pouch = {}
        for item in self.pouch:
            result = self.get_position_pouch(item)
            if result:
                dict_pouch[item] = result
            else:
                self.log_msg("Could not find " + item)
                self.log_msg("Is inventory opened? Does it contain " + item)
                return False
        self.pouch_position = dict_pouch
        return True
    
    def open_inventory(self):
        if self.invetory_open == False:
            self.mouse.move_to(self.win.cp_tabs[3].random_point(), mouseSpeed=self.mouse_speed)
            self.mouse.click()
            self.invetory_open = True


    def get_position_pouch(self, pouch):
        pouch_img = imsearch.BOT_IMAGES.joinpath("altar_bot", pouch +".png")
        if pouch := imsearch.search_img_in_rect(pouch_img, self.win.control_panel):
            return pouch
        return False
        

    def handle_banking(self):
        self.debug("Start open_and_deposit")
        if not self.open_and_deposit():
            return False
        
        self.debug("Start maybe_drink_potion")
        if not self.maybe_drink_potion():
            return False
        
        self.handle_food()

        self.debug("Start get_items_and_close")
        if not self.get_items_and_close():
            return False
        
        return True
            
    def handle_altar(self):
        loop = True
        first = True
        not_clicked_pouch = self.pouch.copy()
     
        while loop:
            if first:
                if not self.click_altar(True):
                    return False
                first = False

                continue

            if self.api_m.get_if_item_in_inv(ids.PURE_ESSENCE):
                self.click_altar(insane_mode=self.insane_mode)
                
            if len(not_clicked_pouch) == 0:
                break

            else:

                if "Colossal_pouch" in self.pouch:

                    self.click_pouch(type_pouch="Colossal_pouch", inventory_change=True,insane_mode=self.insane_mode)
                    if len(self.api_m.get_inv()) == 28:
                        continue

                    if len(self.api_m.get_inv()) != 28:
                        if self.api_m.get_if_item_in_inv(ids.PURE_ESSENCE):
                            self.click_altar()
                        break

                else:
                    random_value = random.choice(not_clicked_pouch)
                    not_clicked_pouch.remove(random_value)
                    self.click_pouch(type_pouch=random_value, inventory_change=True)
                    
        
        return True

    def handle_food(self):
        started = False

        if self.get_hp() < self.panic_stop and self.type_food == "NONE":
            self.debug("Low HP, Stopping")
            self.stop()

        if self.get_hp() < self.panic_stop:
            while self.get_hp() < self.api_m.get_skill_level("Hitpoints") * 0.8:
                started = True
                food_location = self.api_m.get_inv_item_indices(self.type_food_id)
        
                if food_location:
                    self.click_inventory_item(food_location[0])
                    time.sleep(12/10)
                else:
                    food = False
                    while not food: 
                        food_img = imsearch.BOT_IMAGES.joinpath("altar_bot", "Lobster.png")
                        food = imsearch.search_img_in_rect(food_img, self.win.game_view,confidence=0.3)       
                        self.debug("No food found in bank. trying again.")

                    self.mouse.move_to(food.random_point(),mouseSpeed="fastest")
                    self.mouse.click()
                    tries = 0
                    while not self.api_m.get_if_item_in_inv(self.type_food_id):
                        time.sleep(2/10)
                        tries += 1
                        if tries > 10:
                            break
           
                   
            if started:
                self.click_deposit()
            return True
            
            
    def click_inventory_item(self, item_location):
        self.mouse.move_to(self.win.inventory_slots[item_location].random_point(),mouseSpeed="fastest")
        self.mouse.click()
    
    def maybe_click_npc_talk(self):
        if self.api_m.get_if_item_in_inv(ids.COSMIC_RUNE):
            self.debug("Repairing pouch sequence started")
            tries = 0

            time.sleep(2/10)

            while True:
                npc_contact_img = imsearch.BOT_IMAGES.joinpath("altar_bot", "NPC_Contact.png")
                tries = 0
                while not self.mouseover_text("Dark",color=clr.OFF_WHITE):
                    npc_contact = imsearch.search_img_in_rect(npc_contact_img, self.win.control_panel)
                    self.mouse.move_to(npc_contact.random_point(),mouseSpeed=self.mouse_speed)
                    tries = tries + 1
                    
                    if tries > 3:
                        return False
                self.mouse.click()

                self.do_dialogue()
                break
                
                
        return True
    


    def do_dialogue(self):
        time.sleep(3)
        self.do_single_dialogue("1")
        self.do_single_dialogue("2")
        self.do_single_dialogue("3")
        if self.do_single_dialogue("4"):
            return True
    
    def do_single_dialogue(self, dialogue_num):
        dialogue_img = imsearch.BOT_IMAGES.joinpath("altar_bot", "dialogue_" + dialogue_num + ".png")
        dialogue = imsearch.search_img_in_rect(dialogue_img, self.win.chat,confidence=0.01)

        while not dialogue:
            time.sleep(random.randint(400,600)/1000)
            dialogue = imsearch.search_img_in_rect(dialogue_img, self.win.chat,confidence=0.01)

        if dialogue_num == "1" or dialogue_num == "3":
            button = "space"
        elif dialogue_num == "2":
            button = "2"
        elif dialogue_num == "4":
            return True
        
        self.debug("Dialogue  " + dialogue_num + " detected. [" + button + "]")
        pyautogui.press(button)
        time.sleep((random.randint(600,800)/1000))
        
    def click_teleport(self):
        self.mouse.move_to(self.win.cp_tabs[6].random_point(), mouseSpeed=self.mouse_speed)
        self.mouse.click()
        self.invetory_open = False

        ourania_teleport_img = imsearch.BOT_IMAGES.joinpath("altar_bot", "Ourania_Teleport.png")


        ourania_teleport = imsearch.search_img_in_rect(ourania_teleport_img, self.win.control_panel)
        while not ourania_teleport:
            ourania_teleport = imsearch.search_img_in_rect(ourania_teleport_img, self.win.control_panel)
            time.sleep((1/10))
        self.mouse.move_to(ourania_teleport.random_point(),mouseSpeed=self.mouse_speed)

        tries = 0

        # While Fill is not in text, move mouse.
        while not self.mouseover_text(contains="Ouran"):
            # Stop after 5 tries
            
            self.mouse.move_to(ourania_teleport.random_point(),mouseSpeed=self.mouse_speed)
            time.sleep((random.randint(150,250)/1000))

            if tries > 5:           
                self.log_msg('Failed to find Ouran')
                break

        self.mouse.click()

        tries = 0
        lantern = self.get_nearest_tag(clr.BLUE)
        while not lantern:
            time.sleep((random.randint(150,250)/1000))
            lantern = self.get_nearest_tag(clr.BLUE)
            tries = tries + 1
            if tries == 18:
                self.mouse.move_to(ourania_teleport.random_point(),mouseSpeed=self.mouse_speed)
                self.mouse.click()
            if tries == 36:
                return False
        
        #self.log_msg("Locatation changed")
        return True

    def get_items_and_close(self):
        
        # Click pure essence once
        if not self.click_pure_essence():
            return False
        if "Colossal_pouch" in self.pouch:

            self.debug("Colossal pouch first")
            if not self.click_pouch(type_pouch="Colossal_pouch", inventory_change=False, empty_fill="Fill"):
                return False
            # Click pure essence once
            if not self.click_pure_essence():
                return False
            
            self.debug("Colossal pouch second")
            # Click pouch
            if not self.click_pouch(type_pouch="Colossal_pouch", inventory_change=False, empty_fill="Fill"):
                return False
            
            # Click pure essence once
            if not self.click_pure_essence():
                return False
             # Success
            time.sleep((random.randint(1,200)/1000))
            pyautogui.press('esc')  
            return True
            

        
        if 'Small_pouch' in self.pouch:
            self.debug("Small pouch")
            if not self.click_pouch(type_pouch="Small_pouch", inventory_change=False, empty_fill="Fill"):
                self.log_msg("Failed Small")
                return False
            # Click pure essence once
            if not self.click_pure_essence():
                return False
        
        
        if 'Medium_pouch' in self.pouch:
            self.debug("Medium pouch")
            if not self.click_pouch(type_pouch="Medium_pouch", inventory_change=False, empty_fill="Fill"):
                self.log_msg("Medium Failed")
                return False
            # Click pure essence once
            if not self.click_pure_essence():
                return False
            
        if 'Large_pouch' in self.pouch:
            self.debug("Large pouch")
            if not self.click_pouch(type_pouch="Large_pouch", inventory_change=False, empty_fill="Fill"):
                self.log_msg("Large Failed")
                return False
            # Click pure essence once
            if not self.click_pure_essence():
                return False
            
        if 'Giant_pouch' in self.pouch:
            self.debug("Giant pouch")
            if not self.click_pouch(type_pouch="Giant_pouch", inventory_change=False, empty_fill="Fill"):
                self.log_msg("Failed Giant")
                return False
            # Click pure essence once
            if not self.click_pure_essence():
                return False
        # Success
        time.sleep((random.randint(1,200)/1000))
        pyautogui.press('esc')  
        return True
            
        
       
      

    def click_pure_essence(self, inventory_change = False):
         # Get the image path of the pouch
        
        pure_essence_img = imsearch.BOT_IMAGES.joinpath("altar_bot", "Pure_essence.png")

        if inventory_change:
            # Save current inv quantity
            current_inv_qt = len(self.api_m.get_inv())
            time.sleep((random.randint(100,200)/1000))
            new_inv = current_inv_qt
            self.debug('Waiting for inventory change: True')

        while not self.bank_position_essence:
            self.bank_position_essence = imsearch.search_img_in_rect(pure_essence_img, self.win.game_view,confidence=0.05)

    

        # Set tries to 0
        tries = 0

        # While Fill is not in text, move mouse.
        while not self.mouseover_text(contains="Pure"):
            # Stop after 5 tries
            time.sleep(1/10)
            self.mouse.move_to(self.bank_position_essence.random_point(),mouseSpeed=self.mouse_speed)
            

            if tries > 10:
                
                self.log_msg('Failed to find Pure')
                return False
        
        # the actual click
        self.mouse.click()
        if self.insane_mode and "Colossal_pouch" in self.pouch:
            self.mouse.move_to(self.pouch_position["Colossal_pouch"].random_point(),mouseSpeed=self.mouse_speed)

        # If inventory change is true, execute while loop waiting for inventory change
        if inventory_change:
            while current_inv_qt == new_inv:
                if tries > 5:
                    self.log_msg('No inventory change detected')
                    return False
                time.sleep((random.randint(200,250)/1000))
                tries = tries + 1
                new_inv = len(self.api_m.get_inv())
        
        # completed click successfull
        return True

    # Function to click on pouch
    def click_pouch(self, type_pouch , inventory_change = False, empty_fill = "Empty",insane_mode=False):
        if inventory_change:
            # Save current inv quantity
            current_inv_qt = len(self.api_m.get_inv())
            time.sleep(1/10)
            new_inv = current_inv_qt
            self.debug('Waiting for inventory change: True')

        # Set tries to 0
        tries = 0

        # While Fill is not in text, move mouse.
        while not self.mouseover_text(contains=empty_fill):
            # Stop after 5 tries
            pouch = self.pouch_position[type_pouch]
            self.mouse.move_to(pouch.random_point(),mouseSpeed=self.mouse_speed)
            time.sleep(1/10)
            tries = tries + 1
            if empty_fill == "Fill" and self.mouseover_text(contains="Depo"):
                return True
            if tries > 10:
                
                self.log_msg('Failed to find '+ empty_fill)
                return False
        
        # the actual click
        self.mouse.click()
        if insane_mode and empty_fill == "Empty":
            altar = self.get_nearest_tag(color=clr.PINK)
            if altar:
                self.mouse.move_to(altar.random_point(),mouseSpeed=self.mouse_speed)
        elif insane_mode and empty_fill == "Fill":
            if self.bank_position_essence:
                self.mouse.move_to(self.bank_position_essence.random_point(),mouseSpeed=self.mouse_speed)
        
        # If inventory change is true, execute while loop waiting for inventory change
        if inventory_change:
            while current_inv_qt == new_inv:
                if tries > 16:
                    self.log_msg('No inventory change detected')
                    return False
                time.sleep(1/10)
                tries = tries + 1
                new_inv = len(self.api_m.get_inv())

        # completed click successfull
        return True
    
    def maybe_drink_potion(self):
        if self.get_run_energy() < self.min_run_energy:
            stamina_potion1_img = imsearch.BOT_IMAGES.joinpath("altar_bot", "stamina_potion1.png")
            if stamina_potion1 := imsearch.search_img_in_rect(stamina_potion1_img, self.win.game_view):
                # Found image
                # self.log_msg('Move to potion')
                self.mouse.move_to(stamina_potion1.random_point(),mouseSpeed=self.mouse_speed)
            else:
                self.log_msg('Failed to find stamina potions')
                return False
            
            # Save current inv quantity
            current_inv_qt = len(self.api_m.get_inv())
            self.mouse.click()
            tries = 0
            while current_inv_qt == len(self.api_m.get_inv()):
                if tries > 5:
                    self.log_msg('Failed to continue, stopping')
                    return False
                time.sleep(6/10)
                tries = tries + 1

            if stamina_potion1 := imsearch.search_img_in_rect(stamina_potion1_img, self.win.control_panel):
                   # Found image
                # self.log_msg('Move to potion')
                self.mouse.move_to(stamina_potion1.random_point(),mouseSpeed=self.mouse_speed)
            else:
                self.log_msg('Failed to find stamina potions')
                return False
            
            # Save current inv quantity
            current_inv_qt = len(self.api_m.get_inv())
            self.mouse.click()

            while current_inv_qt == len(self.api_m.get_inv()):
                if tries > 5:
                    self.log_msg('Failed to continue, stopping')
                    return False
                time.sleep(6/10)
                tries = tries + 1
            return True
        return True

    def open_and_deposit(self):
        # Get the path to the image
        deposit_all_img = imsearch.BOT_IMAGES.joinpath("altar_bot", "deposit_all.png")
        time.sleep(2/10)
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
            self.last_banker = banker
            # Set a var for keeping the while loop running
            bank_not_opened = True
            tries = 0

            # Run until bank is opened.
            while bank_not_opened:

                # Stop after 5 tries
                if tries > 5:
                    self.log_msg('Failed to continue, stopping')
                    return False
                
                self.mouse.move_to(banker.random_point(),mouseSpeed=self.mouse_speed)
                time.sleep(1/10)
                # Does text match Bank?
                if not self.mouseover_text(contains="Bank"):
                    # If not, start the ladder cyclus again
                    self.debug('Could not locate bank, trying again')
                    banker = self.get_nearest_tag(clr.CYAN)
                    time.sleep(3/10)
                    tries = tries + 1
                    continue

                self.mouse.click()
                if self.deposit_rectangle:
                    deposit_all = imsearch.search_img_in_rect(deposit_all_img, self.deposit_rectangle)
                else:
                    deposit_all = False
                # Waiting till player is idle
                move_to = False
                while not deposit_all:
             
                    if not self.deposit_rectangle:
                        deposit_all = imsearch.search_img_in_rect(deposit_all_img, self.win.game_view)
                        if deposit_all:
                            self.deposit_rectangle = deposit_all
                            
                        else:
                            if not move_to and self.deposit_rectangle:
                                self.mouse.move_to(self.deposit_rectangle.random_point(),mouseSpeed=self.mouse_speed) 
                            time.sleep(1/10)
                            continue
                    else:
                        
                        deposit_all = imsearch.search_img_in_rect(deposit_all_img, self.deposit_rectangle)
                        
                
                self.debug("bank opened")

                if len(self.api_m.get_inv()) > len(self.pouch) + 1:
                    self.click_deposit()
                return True
    def click_deposit(self):
        # While Deposit is not in text, move mouse.
        deposit_all_img = imsearch.BOT_IMAGES.joinpath("altar_bot", "deposit_all.png")
        tries = 0
        while not self.mouseover_text(contains="inventory"):
            # Stop after 5 tries
            if tries > 5:
                self.log_msg('Failed to continue, stopping')
                return False
            
            
            if deposit_all := imsearch.search_img_in_rect(deposit_all_img, self.win.game_view):
                # Found image
                self.mouse.move_to(deposit_all.random_point(),mouseSpeed=self.mouse_speed)
            else:
                self.log_msg('Failed to find deposit all')
                tries = tries + 1
                continue
        
        
        # Save current inv quantity
        current_inv_qt = len(self.api_m.get_inv())

        # Click to deposit
        self.mouse.click()

        time.sleep(1/10)
     
        while current_inv_qt == len(self.api_m.get_inv()):
     
            if tries > 10:
                self.log_msg('Failed to continue, stopping')
                return False
            time.sleep(2/10)
            tries = tries + 1

    def click_altar(self, first = False, insane_mode=False):
        tries = 0
        toggle_run = False
        # Find 
        altar = self.get_nearest_tag(clr.PINK)
        while not altar:
            time.sleep(1/10)
            self.debug("cant find altar, trying again")
            altar = self.get_nearest_tag(clr.PINK)

        altar_not_found = True
        while not self.mouseover_text("Craft"):
            altar = self.get_nearest_tag(clr.PINK)
            self.mouse.move_to(altar.random_point(), mouseSpeed=self.mouse_speed)
            if first:
                
                self.mouse.right_click()
                time.sleep(1/10)

                craft_runes_img = imsearch.BOT_IMAGES.joinpath("altar_bot", "craft_rune.png")
                craft_runes = imsearch.search_img_in_rect(craft_runes_img, self.win.game_view)
                tries = 0
                while not craft_runes:
                    self.mouse.move_to(self.win.game_view.random_point(),mouseSpeed=self.mouse_speed)
                    altar = self.get_nearest_tag(clr.PINK)
                    if altar:
                        self.mouse.move_to(altar.random_point(), mouseSpeed=self.mouse_speed)
                        self.mouse.right_click()
                    tries += 1
                    if tries > 5:
                        return False
                    time.sleep(3/10)
                    craft_runes = imsearch.search_img_in_rect(craft_runes_img, self.win.game_view)
                    
                    
                self.mouse.move_to(craft_runes.random_point(), mouseSpeed=self.mouse_speed)
                break
                 
        current_inv_qt = len(self.api_m.get_inv()) 
        self.mouse.click()    
        
        if first:
            time.sleep(3)
            if insane_mode and "Colossal_pouch" in self.pouch:
                self.mouse.move_to(self.pouch_position["Colossal_pouch"].random_point(),mouseSpeed=self.mouse_speed)
        else:
            if insane_mode and "Colossal_pouch" in self.pouch:
                self.mouse.move_to(self.pouch_position["Colossal_pouch"].random_point(),mouseSpeed=self.mouse_speed)

        while current_inv_qt == len(self.api_m.get_inv()):
            if first:
                if not self.invetory_open:
                    if rd.random_chance(probability=0.01):
                        # Click the inventory tab
                        self.open_inventory()
                        if insane_mode and "Colossal_pouch" in self.pouch:
                            self.mouse.move_to(self.pouch_position["Colossal_pouch"].random_point(),mouseSpeed=self.mouse_speed)
                if not toggle_run:
                    
                    #self.toggle_run(toggle_on=True)
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
                self.open_inventory()
                if insane_mode and "Colossal_pouch" in self.pouch:
                    self.mouse.move_to(self.pouch_position["Colossal_pouch"].random_point(),mouseSpeed=self.mouse_speed)
        return True
        

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
            self.mouse.move_to(ladder.random_point(), mouseSpeed=self.mouse_speed)
            time.sleep(1/10)
            if not self.mouseover_text("Climb",color=clr.OFF_WHITE):
                self.mouse.right_click()
                time.sleep(1/10)

                climb_ladder_img = imsearch.BOT_IMAGES.joinpath("altar_bot", "climb_ladder.png")
                climb_ladder = imsearch.search_img_in_rect(climb_ladder_img, self.win.game_view)

                while not climb_ladder:
                    
                    
                    self.mouse.move_to(self.win.game_view.random_point())
                    ladder = self.get_nearest_tag(clr.BLUE)
                    if ladder:
                        self.mouse.move_to(ladder.random_point(),mouseSpeed=self.mouse_speed)
                        time.sleep(2/10)
                        self.mouse.right_click()
                    time.sleep(2/10)
                    climb_ladder = imsearch.search_img_in_rect(climb_ladder_img, self.win.game_view)
                    tries = tries + 1
                    
                    
                self.mouse.move_to(climb_ladder.random_point(), mouseSpeed=self.mouse_speed)
            
            # Found climb, clicking ladder
            self.mouse.click()

            # Sleep for 1 second
            time.sleep(1)        

            # Waiting till player is idle
            while not self.api_m.get_is_player_idle():
                time.sleep(3/10)
                if not self.invetory_open:
                    if rd.random_chance(probability=0.05):
                        # Click the inventory tab
                        self.open_inventory()
                        if self.last_banker:
                            self.mouse.move_to(self.last_banker.random_point(),mouseSpeed=self.mouse_speed)
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

