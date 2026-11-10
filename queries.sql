Create database Olaride_insights;
use Olaride_insights;
select*
from ola;
-- 1. Retrieve all successful bookings
Select Booking_Status as Success_booking
from ola
where Booking_Status='Success';
-- 2. Find the average ride distance for each vehicle type
SELECT
    Vehicle_Type,
    AVG(Ride_Distance) AS Average_Ride_Distance
FROM ola
GROUP BY Vehicle_Type;
-- 3. Get the total number of cancelled rides by customers:
select distinct count('Canceled_Rides_by_Customer')
from ola;
-- 4. List the top 5 customers who booked the highest number of rides:
SELECT
    Customer_ID,
    COUNT(Booking_ID) AS Total_Rides
FROM ola
GROUP BY Customer_ID
ORDER BY Total_Rides DESC
LIMIT 5;
-- 5. Get the number of rides cancelled by drivers due to personal and car-related issues
select distinct count('Canceled_Rides_by_Driver')
from ola
where Canceled_Rides_by_Driver='Personal & Car related issue';
-- 6. Find the maximum and minimum driver ratings for Prime Sedan bookings:
select max(Driver_Ratings) as Maximun, min(Driver_Ratings) as Minimum
from ola
where Vehicle_Type='Prime Sedan';
-- 7. Retrieve all rides where payment was made using UPI:
select*
from ola
where Payment_Method='UPI';

select Booking_Status, Payment_Method
from ola
where Payment_Method='UPI';
-- 8. Find the average customer rating per vehicle type:
Select Vehicle_Type,
avg(Customer_Rating)
from ola 
group by Vehicle_Type;
-- 9. Calculate the total booking value of rides completed successfully
select sum(Booking_Value) as Total_value
from ola 
where Booking_Status='Success';
-- 10. List all incomplete rides along with the reason
SELECT
    Incomplete_Rides,
    Incomplete_Rides_Reason
FROM ola
where Incomplete_Rides ='yes';
SELECT
    Booking_ID,
    Booking_Status,
    Customer_ID,
    Vehicle_Type,
    Pickup_Location,
    Drop_Location,
    Incomplete_Rides_Reason
FROM
    ola
WHERE
    Incomplete_Rides != 'Completed or Canceled'
    AND Incomplete_Rides_Reason != 'Not Applicable'
ORDER BY
    Booking_ID;











