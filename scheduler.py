import schedule
import time
from SiteChecker import main  # Assuming your SiteChecker script has a `main` function

# Define a job to run SiteChecker.py daily
def job():
    print("Running SiteChecker script...")
    main()  # Call the main function from SiteChecker.py

# Schedule the job to run daily at a specific time (e.g., at 9:00 AM)
schedule.every().day.at("09:00").do(job)

# Keep the script running to execute the task
while True:
    schedule.run_pending()
    time.sleep(60)  # Wait 1 minute before checking again
