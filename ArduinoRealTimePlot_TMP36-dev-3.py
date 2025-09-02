import time
import serial
import datetime
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from tkinter import Tk, Button, Label, Frame
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.backends.backend_pdf
import numpy as np
import csv

# Global variables
is_running = False

temp_buffer1, temp_buffer2, temp_buffer3 = [], [], []
time_buffer = []

temperature_list1 = []
temperature_list2 = []
temperature_list3 = []

time_list = []  # To store real-time timestamps

ani = None

# Fixed run time of 2 hours
run_duration = datetime.timedelta(hours=6)  # 2 hours duration
#run_duration = datetime.timedelta(minutes=1)  # 1 minutes duration
start_time = None
end_time = None

today_time = datetime.datetime.now()

# Function to start animation
def start_animation():
    global is_running, ani, start_time, end_time
    if not is_running:
        is_running = True
        start_time = datetime.datetime.now()  # Set start time
        end_time = start_time + run_duration  # Set end time after 2 hours
        ani.event_source.start()  # Start the animation
        status_label.config(text="Status: Running", fg="green")

# Function to stop animation
def stop_animation():
    global is_running, ani
    if is_running:
        is_running = False
        ani.event_source.stop()  # Stop the animation
        status_label.config(text="Status: Stopped", fg="red")
        save_data_to_files()  # Save the data after stopping

# Function to close application
def close_app():
    global ser
    if ser.is_open:
        ser.close()  # Close the serial port
    root.quit()  # Close the Tkinter window
    print("Data saved to temperature_data_{}.csv".format(today_time.date()))

# Function to save the plot to PDF and PNG
def save_data_to_files():
    print("Saving data to PDF and PNG...")
    # Save as PDF
    pdf = matplotlib.backends.backend_pdf.PdfPages("sensor_data_output_{}.pdf".format(today_time.date()))
    pdf.savefig(fig)  # Save the current figure to the PDF
    pdf.close()
    print("Data saved to 'sensor_data_output_{}.pdf'.".format(today_time.date()))

    # Save as PNG
    fig.savefig("sensor_data_output_{}.png".format(today_time.date()), bbox_inches="tight")  # Save as PNG
    print("Data saved to 'sensor_data_output_{}.png'.".format(today_time.date()))

# Animation function
def animate(i, ser):
    if is_running:  # Ensure data is plotted only when running
        global temperature_list1, temperature_list2, temperature_list3, time_list

        # Check if the current time exceeds the end time (2 hours)
        if datetime.datetime.now() >= end_time:
            stop_animation()  # Stop animation after 2 hours
            return

        # Read and decode data from the serial port
        try:
            ser.write(b'g')  # Trigger data transmission
            arduino_data = ser.readline().decode('ascii').strip()
            print(f"Received: {arduino_data}")

            # Parse the received data
            temperature1, temperature2, temperature3 = map(float, arduino_data.split(","))

            # Get the current time
            current_time = datetime.datetime.now()
            #print("current time = ", current_time)

            # Append the new data to the buffers
            temp_buffer1.append(temperature1)
            temp_buffer2.append(temperature2)
            temp_buffer3.append(temperature3)
            time_buffer.append(current_time)


            # Check if the buffers have collected 10 points
            if len(temp_buffer1) == 4:
                # Calculate the averages
                avg_temp1 = np.mean(temp_buffer1)
                avg_temp2 = np.mean(temp_buffer2)
                avg_temp3 = np.mean(temp_buffer3)

                # Calculate average timestamp (in seconds)
                avg_time_seconds = sum((t - time_buffer[0]).total_seconds() for t in time_buffer) / len(time_buffer)

                # Add the average seconds to the first timestamp to get the average datetime
                avg_time = time_buffer[0] + datetime.timedelta(seconds=avg_time_seconds)

                # Append the averages to the main lists
                temperature_list1.append(avg_temp1)
                temperature_list2.append(avg_temp2)
                temperature_list3.append(avg_temp3)
                time_list.append(avg_time)

                #print("Avg T1 = ", temperature_list1)
                #print("Avg Time = ", time_list)

                # Clear the buffers
                temp_buffer1.clear()
                temp_buffer2.clear()
                temp_buffer3.clear()
                time_buffer.clear()

            # Clear and update the plots
            ax1.clear()

            # Plot Temperature
            ax1.plot(time_list, temperature_list1, label="Temperature (°C) (TMP36-1)", color="red")
            ax1.plot(time_list, temperature_list2, label="Temperature (°C) (TMP36-2)", color="blue")
            ax1.plot(time_list, temperature_list3, label="Temperature (°C) (TMP36-3)", color="green")
            ax1.set_ylim([-50, 50])
            ax1.set_title("Temperature Data")
            ax1.set_ylabel("Temperature (°C)")
            ax1.legend(loc="upper right")
            ax1.grid()

            # Format the X-axis to show time in minutes
            ax1.xaxis_date()
            fig.autofmt_xdate()

            # Prepare the data to be saved
            data = zip(time_list, temperature_list1, temperature_list2, temperature_list3)
            filename = "temperature_data_{}.csv".format(current_time.date())

            # Write to CSV
            with open(filename, mode='w', newline='') as file:
                writer = csv.writer(file)

                # Write header
                writer.writerow(['Time', 'Temperature 1 (°C)', 'Temperature 2 (°C)', 'Temperature 3 (°C)'])

                # Write data
                for row in data:
                    # Convert datetime to string format for saving

                    # Round the temperature values to 2 decimal places
                    rounded_temp1 = round(row[1], 2)
                    rounded_temp2 = round(row[2], 2)
                    rounded_temp3 = round(row[3], 2)
       
                    writer.writerow([row[0].strftime('%Y-%m-%d %H:%M:%S')] + [rounded_temp1, rounded_temp2, rounded_temp3])
                    #writer.writerow([row[0].strftime('%Y-%m-%d %H:%M:%S')] + list(row[1:]))

            #print("Data saved to", filename)

        except Exception as e:
            print(f"Error: {e}")

# Tkinter GUI setup
root = Tk()
root.title("Real-Time Arduino Data Logger")

# Serial setup
ser = serial.Serial("/dev/ttyACM0", 9600)  # Update with your port
time.sleep(2)  # Allow Arduino to initialize

# Matplotlib Figure
fig, ax1 = plt.subplots(figsize=(10, 6))
plt.tight_layout()

# Embedding Matplotlib in Tkinter
canvas = FigureCanvasTkAgg(fig, master=root)
plot_widget = canvas.get_tk_widget()
plot_widget.pack()

# GUI Buttons and Status Label
button_frame = Frame(root)
button_frame.pack()

# Define font for buttons and status label
button_font = ("Arial", 14, "bold")  # Larger font for buttons
status_font = ("Arial", 12, "bold")  # Larger font for status label

# Buttons
start_button = Button(button_frame, text="Start", command=start_animation, bg="green", fg="white", font=button_font)
start_button.grid(row=0, column=0, padx=15, pady=10)

stop_button = Button(button_frame, text="Stop", command=stop_animation, bg="red", fg="white", font=button_font)
stop_button.grid(row=0, column=1, padx=15, pady=10)

exit_button = Button(button_frame, text="Exit", command=close_app, bg="black", fg="white", font=button_font)
exit_button.grid(row=0, column=2, padx=15, pady=10)

# Status Label
status_label = Label(button_frame, text="Status: Stopped", fg="red", font=status_font)
status_label.grid(row=1, column=0, columnspan=3, pady=10)

# Matplotlib Animation
ani = animation.FuncAnimation(fig, animate, fargs=(ser,), interval=1000)
ani.event_source.stop()  # Ensure animation is stopped initially

# Main loop
root.protocol("WM_DELETE_WINDOW", close_app)  # Ensure serial port closes on exit
root.mainloop()

