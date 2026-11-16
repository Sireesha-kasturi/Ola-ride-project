# SQL questions for the OLA Ride Insights Streamlit application.
# The app creates an SQLite table named `ola_rides`.

QUERIES = {'1. Retrieve all successful bookings': {'sql': 'SELECT *\n'
                                                'FROM ola_rides\n'
                                                "WHERE Booking_Status = 'Success';",
                                         'note': 'All bookings with successful status.',
                                         'view': 'successful_bookings'},
 '2. Average ride distance for each vehicle type': {'sql': 'SELECT Vehicle_Type,\n'
                                                           '       ROUND(AVG(Ride_Distance), 2) AS '
                                                           'Average_Ride_Distance\n'
                                                           'FROM ola_rides\n'
                                                           'GROUP BY Vehicle_Type\n'
                                                           'ORDER BY Average_Ride_Distance DESC;',
                                                    'note': 'Average ride distance grouped by '
                                                            'vehicle type.',
                                                    'view': 'average_distance_by_vehicle'},
 '3. Total number of rides cancelled by customers': {'sql': 'SELECT COUNT(*) AS '
                                                            'Customer_Cancelled_Rides\n'
                                                            'FROM ola_rides\n'
                                                            "WHERE Cancelled_By = 'Customer';",
                                                     'note': 'Counts bookings cancelled by '
                                                             'customers.',
                                                     'view': 'customer_cancelled_rides'},
 '4. Top 5 customers by number of booked rides': {'sql': 'SELECT Customer_ID,\n'
                                                         '       COUNT(Booking_ID) AS Total_Rides\n'
                                                         'FROM ola_rides\n'
                                                         'GROUP BY Customer_ID\n'
                                                         'ORDER BY Total_Rides DESC\n'
                                                         'LIMIT 5;',
                                                  'note': 'Five customers with the highest booking '
                                                          'counts.',
                                                  'view': 'top_5_customers'},
 '5. Driver cancellations due to personal and car-related issues': {'sql': 'SELECT COUNT(*) AS '
                                                                           'Driver_Cancellations_Personal_Car_Issues\n'
                                                                           'FROM ola_rides\n'
                                                                           'WHERE Cancelled_By = '
                                                                           "'Driver'\n"
                                                                           '  AND '
                                                                           'Canceled_Rides_by_Driver '
                                                                           "= 'Personal & Car "
                                                                           "related issue';",
                                                                    'note': 'Counts driver '
                                                                            'cancellations for the '
                                                                            'specified reason.',
                                                                    'view': 'driver_cancellations_personal_car_issues'},
 '6. Maximum and minimum driver ratings for Prime Sedan': {'sql': 'SELECT MAX(Driver_Ratings) AS '
                                                                  'Maximum_Driver_Rating,\n'
                                                                  '       MIN(Driver_Ratings) AS '
                                                                  'Minimum_Driver_Rating\n'
                                                                  'FROM ola_rides\n'
                                                                  "WHERE Vehicle_Type = 'Prime "
                                                                  "Sedan';",
                                                           'note': 'Highest and lowest driver '
                                                                   'ratings for Prime Sedan '
                                                                   'bookings.',
                                                           'view': 'prime_sedan_driver_ratings'},
 '7. All rides paid using UPI': {'sql': "SELECT *\nFROM ola_rides\nWHERE Payment_Method = 'UPI';",
                                 'note': 'Bookings where the payment method is UPI.',
                                 'view': 'upi_rides'},
 '8. Average customer rating per vehicle type': {'sql': 'SELECT Vehicle_Type,\n'
                                                        '       ROUND(AVG(Customer_Rating), 2) AS '
                                                        'Average_Customer_Rating\n'
                                                        'FROM ola_rides\n'
                                                        'GROUP BY Vehicle_Type\n'
                                                        'ORDER BY Average_Customer_Rating DESC;',
                                                 'note': 'Average customer rating grouped by '
                                                         'vehicle type.',
                                                 'view': 'average_customer_rating'},
 '9. Total booking value of successful rides': {'sql': 'SELECT ROUND(SUM(Booking_Value), 2) AS '
                                                       'Total_Successful_Booking_Value\n'
                                                       'FROM ola_rides\n'
                                                       "WHERE Booking_Status = 'Success';",
                                                'note': 'Sum of booking value for successful '
                                                        'rides.',
                                                'view': 'successful_booking_value'},
 '10. Incomplete rides with their reasons': {'sql': 'SELECT Booking_ID,\n'
                                                    '       Incomplete_Rides,\n'
                                                    '       Incomplete_Rides_Reason\n'
                                                    'FROM ola_rides\n'
                                                    'WHERE LOWER(CAST(Incomplete_Rides AS TEXT)) = '
                                                    "'yes'\n"
                                                    "  AND COALESCE(Incomplete_Rides_Reason, '') "
                                                    "NOT IN ('', 'Not Applicable')\n"
                                                    'ORDER BY Booking_ID;',
                                             'note': 'Incomplete rides and the recorded reason.',
                                             'view': 'incomplete_rides'}}
