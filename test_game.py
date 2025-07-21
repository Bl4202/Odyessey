import traceback

try:
    import game_gui
    # Create and run the game
    game = game_gui.GameGUI()
    game.run()
except Exception as e:
    print(f"Error occurred: {str(e)}")
    traceback.print_exc()