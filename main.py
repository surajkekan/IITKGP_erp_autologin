import sys
import logging
from src.app import ERPApp

def main():
    debug_mode = "--debug" in sys.argv
    level = logging.DEBUG if debug_mode else logging.INFO
    
    # Configure logging to show in terminal
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )
    
    if debug_mode:
        logging.info("Debug mode enabled.")
    
    app = ERPApp()
    app.mainloop()

if __name__ == "__main__":
    main()
