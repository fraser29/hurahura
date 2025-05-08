from nicegui import ui
import os

# Module-level variable to store the MIResearchUI instance
_the_miui_instance = None

def initialize_settings_ui(miui_instance_from_main):
    """Stores the MIResearchUI instance for the settings page to use."""
    global _the_miui_instance
    _the_miui_instance = miui_instance_from_main

@ui.page('/miui_settings')
def display_settings_page_standalone():
    """The dedicated page for displaying MIUI settings."""
    if _the_miui_instance:
        create_settings_page(_the_miui_instance) # Call the existing layout function
    else:
        ui.label("Error: Settings UI not initialized correctly. MIResearchUI instance is missing.").classes('text-red-500')
        ui.button("Go Home", on_click=lambda: ui.navigate.to('/'))

def create_settings_page(miui_instance):
    """
    Creates the settings page for the MIResearchUI.

    Args:
        miui_instance: An instance of the MIResearchUI class.
    """
    conf_files_dict = miui_instance.miui_conf_file_contents

    # Define helper functions first
    def display_config_content(selected_key):
        if selected_key and selected_key in conf_files_dict:
            file_path = conf_files_dict[selected_key]
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                content_display.set_text(f"File source: {file_path}")
                content_editor.set_value(content)
                file_content_area.visible = True
            except Exception as e:
                ui.notify(f"Error reading file {file_path}: {e}", type='negative')
                content_display.set_text(f"Could not load file: {file_path}")
                content_editor.set_value('')
        else:
            content_display.set_text('')
            content_editor.set_value('')
            file_content_area.visible = False
    
    async def save_changes(selected_key, new_content):
        if selected_key and selected_key in conf_files_dict:
            file_path = conf_files_dict[selected_key]
            try:
                with open(file_path, 'w') as f:
                    f.write(new_content)
                ui.notify(f"Saved changes to {file_path}", type='positive')
                # Refresh content display
                display_config_content(selected_key)
            except Exception as e:
                ui.notify(f"Error saving file {file_path}: {e}", type='negative')
        else:
            ui.notify("No file selected or key not found.", type='warning')

    def process_new_config(key, path, dialog_ref):
        if not key or not path:
            ui.notify("Both key and path are required.", type='warning')
            return

        if key in conf_files_dict:
            ui.notify(f"Configuration key '{key}' already exists.", type='warning')
            return
        
        try:
            if not os.path.exists(os.path.dirname(path)):
                 os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'a'): 
                os.utime(path, None) 
            
            miui_instance._saveMIUI_ConfigFile([path])
            
            conf_files_dict[key] = path
            config_keys_select.options = list(conf_files_dict.keys())
            config_keys_select.update()
            ui.notify(f"Added new config: '{key}' pointing to '{path}'", type='positive')
            dialog_ref.close()

        except Exception as e:
            ui.notify(f"Error adding new config file: {e}", type='negative')

    async def add_new_config_dialog():
        with ui.dialog() as dialog, ui.card():
            ui.label('Add New Configuration File').classes('text-lg font-semibold')
            new_conf_key_input = ui.input(label='Configuration Key Name')
            new_conf_path_input = ui.input(label='Full Path to New Config File')
            
            with ui.row():
                ui.button('Save New Config', on_click=lambda: process_new_config(new_conf_key_input.value, new_conf_path_input.value, dialog))
                ui.button('Cancel', on_click=dialog.close)
        await dialog

    # UI layout starts here
    with ui.column().classes('w-full p-4'):
        with ui.row().classes('w-full items-center mb-4'):
            ui.button(icon='home', on_click=lambda: ui.navigate.to('/')).props('flat round dense').tooltip('Go to Home Page')
            ui.label('MIUI Configuration Files').classes('text-2xl font-bold ml-2')

        with ui.row().classes('w-full mb-4'):
            ui.label(f'Configuration Keys (saved at {miui_instance.miui_conf_file}):').classes('text-lg mr-2')
            config_keys_select = ui.select(list(conf_files_dict.keys()), 
                                           label='Select Config', 
                                           on_change=lambda e: display_config_content(e.value))
            
        file_content_area = ui.column().classes('w-full p-2 border rounded')
        with file_content_area:
            ui.label(f'File Content:').classes('text-lg font-semibold mb-2')
            content_display = ui.label('').classes('text-mono whitespace-pre-wrap')
            content_editor = ui.textarea(label='Edit Content').classes('w-full').props('outlined rows=10')
            
        with ui.row().classes('w-full mt-4'):
            ui.button('Save Changes', on_click=lambda: save_changes(config_keys_select.value, content_editor.value))
            ui.button('Add New Config File', on_click=add_new_config_dialog)

    file_content_area.visible = False
