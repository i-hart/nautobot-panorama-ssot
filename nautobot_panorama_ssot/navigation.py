"""Navigation menu items for Panorama SSOT."""
from nautobot.apps.ui import NavMenuAddButton, NavMenuGroup, NavMenuItem, NavMenuTab


menu_items = (
    NavMenuTab(
        name="Plugins",
        groups=(
            NavMenuGroup(
                name="Panorama SSOT",
                weight=100,
                items=(
                    NavMenuItem(
                        link="plugins:nautobot_panorama_ssot:panoramainstance_list",
                        name="Panorama Instances",
                        permissions=["nautobot_panorama_ssot.view_panoramainstance"],
                        buttons=(
                            NavMenuAddButton(
                                link="plugins:nautobot_panorama_ssot:panoramainstance_add",
                                permissions=["nautobot_panorama_ssot.add_panoramainstance"],
                            ),
                        ),
                    ),
                ),
            ),
        ),
    ),
)
