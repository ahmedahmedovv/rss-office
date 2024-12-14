from multiprocessing import Process
import app
import main

def run_flask():
    # Remove debug=True when running with multiprocessing
    app.app.run(host='0.0.0.0', port=5000, debug=True)

def run_fetcher():
    main.main()

if __name__ == '__main__':
    # Create processes
    flask_process = Process(target=run_flask)
    fetcher_process = Process(target=run_fetcher)
    
    try:
        # Start processes
        flask_process.start()
        fetcher_process.start()
        
        # Wait for processes to complete
        flask_process.join()
        fetcher_process.join()
    except KeyboardInterrupt:
        print("\nShutting down processes...")
        flask_process.terminate()
        fetcher_process.terminate()
        flask_process.join()
        fetcher_process.join()
        print("Processes terminated successfully") 