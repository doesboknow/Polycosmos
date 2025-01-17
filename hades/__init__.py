import string
import typing
import settings

from BaseClasses import Entrance, Item, ItemClassification, Location, MultiWorld, Region, Tutorial
from .Items import item_table, item_table_pacts, HadesItem, event_item_pairs, create_pact_pool_amount, create_filler_pool_options, item_table_keepsake
from .Locations import setup_location_table_with_settings, give_all_locations_table, HadesLocation
from .Options import hades_options
from .Regions import create_regions
from .Rules import set_rules
from worlds.AutoWorld import WebWorld, World
from worlds.LauncherComponents import Component, components, Type, launch_subprocess


def launch_client():
    from .Client import launch
    launch_subprocess(launch, "HadesClient")


components.append(Component("Hades Client", "HadesClient", func=launch_client, component_type=Type.CLIENT))


class HadesSettings(settings.Group):
    class StyxScribePath(settings.UserFilePath):
        """Path to the StyxScribe install"""

    styx_scribe_path: StyxScribePath = StyxScribePath("C:/Program Files/Steam/steamapps/common/Hades/StyxScribe.py")


class HadesWeb(WebWorld):
    tutorials = [Tutorial(
        "Multiworld Setup Guide",
        "A guide to setting up Hades for Archipelago. "
        "This guide covers single-player, multiworld, and related software.",
        "English",
        "Hades.md",
        "Hades/en",
        ["Naix"]
    )]


class HadesWorld(World):
    """
    Hades is a rogue-like dungeon crawler in which you defy the god of the dead as you hack and slash your way out of the Underworld of Greek myth.
    """

    option_definitions = hades_options
    game = "Hades"
    topology_present = False
    data_version = 1
    settings: typing.ClassVar[HadesSettings]
    web = HadesWeb()
    required_client_version = (0, 4, 4)
    
    polycosmos_version = "0.5.2"

    item_name_to_id = {name: data.code for name, data in item_table.items()}
    location_table = give_all_locations_table()
    location_name_to_id = location_table

    def generate_early(self):
        self.location_table = setup_location_table_with_settings(self.options)
        self.location_name_to_id = self.location_table

    def create_items(self):  
        self.location_table = setup_location_table_with_settings(self.options)
        self.location_name_to_id = self.location_table
        
        pool = []

        #Fill pact items
        item_pool_pacts = create_pact_pool_amount(self.options)

        #Fill pact items
        for name, data in item_table_pacts.items():
            for amount in range(item_pool_pacts.get(name, 1)):
                item = HadesItem(name, self.player)
                pool.append(item)
        
        #Fill keepsake items
        if (self.options.keepsakesanity.value==1):
            for name, data in item_table_keepsake.items():
                item = HadesItem(name, self.player)
                pool.append(item)

        #create the pack of filler options
        filler_options = create_filler_pool_options(self.options)

        #Fill filler items uniformly. Maybe later we can tweak this.
        index = 0
        for amount in range(0, len(self.location_name_to_id)-len(pool)):
            item_name = filler_options[index]
            item = HadesItem(item_name, self.player)
            pool.append(item)
            index = (index+1)%len(filler_options)
        
        self.multiworld.itempool += pool


        # Pair up our event locations with our event items
        for event, item in event_item_pairs.items():
            event_item = HadesItem(item, self.player)
            self.multiworld.get_location(event, self.player).place_locked_item(event_item)

    def set_rules(self):
        self.location_table = setup_location_table_with_settings(self.options)
        self.location_name_to_id = self.location_table
        
        set_rules(self.multiworld, self.player, self.calculate_number_of_pact_items(), self.location_table, self.options)

    def calculate_number_of_pact_items(self):
        #Go thorugh every option and count what is the chosen level
        total = int(self.options.hard_labor_pact_amount.value)
        total += int(self.options.lasting_consequences_pact_amount.value)
        total += int(self.options.convenience_fee_pact_amount.value)
        total += int(self.options.jury_summons_pact_amount.value)
        total += int(self.options.extreme_measures_pact_amount.value)
        total += int(self.options.calisthenics_program_pact_amount.value)
        total += int(self.options.benefits_package_pact_amount.value)
        total += int(self.options.middle_management_pact_amount.value)
        total += int(self.options.underworld_customs_pact_amount.value)
        total += int(self.options.forced_overtime_pact_amount.value)
        total += int(self.options.heightened_security_pact_amount.value)
        total += int(self.options.routine_inspection_pact_amount.value)
        total += int(self.options.damage_control_pact_amount.value)
        total += int(self.options.approval_process_pact_amount.value)
        total += int(self.options.tight_deadline_pact_amount.value)
        total += int(self.options.personal_liability_pact_amount.value)
        return total

    def create_item(self, name: str) -> Item:
        return HadesItem(name, self.player)

    def create_regions(self):
        self.location_table = setup_location_table_with_settings(self.options)
        self.location_name_to_id = self.location_table
        
        create_regions(self, self.location_table)


    def fill_slot_data(self) -> dict:
        slot_data = {
            'seed': "".join(self.multiworld.per_slot_randoms[self.player].choice(string.ascii_letters) for i in range(16))
        }
        for option_name in hades_options:
            option = getattr(self.options, option_name)
            slot_data[option_name] = option.value
        slot_data["version_check"] = self.polycosmos_version
        return slot_data

    def get_filler_item_name(self) -> str:
        return "Darkness"


def create_region(world: MultiWorld, player: int, location_database, name: str, locations=None, exits=None):
    ret = Region(name, player, world)
    if locations:
        for location in locations:
            loc_id = location_database.get(location, 0)
            location = HadesLocation(player, location, loc_id, ret)
            ret.locations.append(location)
    if exits:
        for exit in exits:
            ret.exits.append(Entrance(player, exit, ret))

    return ret

