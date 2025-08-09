import os
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import pandas as pd
from amadeus import Client, ResponseError


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('flight_data_collection.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class FlightDataCollector:
    def __init__(self):
        self.amadeus = self._initialize_amadeus_client()
        self.collected_flights = []
        self.routes = [
            {"origin": "MAD", "destination": "BCN", "route_name": "Madrid to Barcelona"},
            {"origin": "JFK", "destination": "LAX", "route_name": "New York to Los Angeles"},
            {"origin": "BER", "destination": "PAR", "route_name": "Berlin to Paris"},
            {"origin": "LON", "destination": "SFO", "route_name": "London to San Francisco"},
        ]
    
    def _initialize_amadeus_client(self) -> Client:
        amadeus_api_key = st.secrets["AMADEUS_API_KEY"]
        amadeus_api_secret = st.secrets["AMADEUS_API_SECRET"]
        if not api_key or not api_secret:
            raise ValueError("Amadeus API credentials not found in environment variables")
        return Client(client_id=api_key, client_secret=api_secret)
    
    def search_flights(self, origin: str, destination: str, departure_date: str) -> List[Dict]:
        try:
            response = self.amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=destination,
                departureDate=departure_date,
                adults=1,
                max=50
            )
            return response.data
        except ResponseError as error:
            logger.error(f"Amadeus API error for {origin} to {destination} on {departure_date}: {error}")
            print(f"Amadeus API error for {origin} to {destination} on {departure_date}: {error}")
            raise SystemExit("Stopping program due to API error.")
        except Exception as error:
            logger.error(f"Unexpected error: {error}")
            print(f"Unexpected error: {error}")
            raise SystemExit("Stopping program due to unexpected error.")
    
    def parse_flight_data(self, flight_offers: List[Dict], route_name: str, origin: str, destination: str) -> List[Dict]:
        parsed_flights = []
        airline_codes = {
            'AA': 'American Airlines', 'DL': 'Delta Air Lines', 'UA': 'United Airlines',
            'BA': 'British Airways', 'AF': 'Air France', 'LH': 'Lufthansa',
            'CX': 'Cathay Pacific', 'JL': 'Japan Airlines', 'NH': 'All Nippon Airways',
            'AC': 'Air Canada', 'WN': 'Southwest Airlines', 'AS': 'Alaska Airlines',
            'B6': 'JetBlue Airways', 'F9': 'Frontier Airlines', 'NK': 'Spirit Airlines',
            'G4': 'Allegiant Air'
        }
        
        for offer in flight_offers:
            try:
                itinerary = offer['itineraries'][0]
                segments = itinerary['segments']
                first_segment = segments[0]
                last_segment = segments[-1]
                
                flight_data = {
                    'route_name': route_name,
                    'origin': first_segment['departure']['iataCode'],
                    'destination': last_segment['arrival']['iataCode'],
                    'departure_date': first_segment['departure']['at'][:10],
                    'arrival_date': last_segment['arrival']['at'][:10],
                    'departure_time': first_segment['departure']['at'][11:19],
                    'arrival_time': last_segment['arrival']['at'][11:19],
                    'airline_code': first_segment['carrierCode'],
                    'airline_name': airline_codes.get(first_segment['carrierCode'], first_segment['carrierCode']),
                    'flight_number': f"{first_segment['carrierCode']}{first_segment['number']}",
                    'aircraft_code': first_segment.get('aircraft', {}).get('code', 'N/A'),
                    'price_amount': float(offer['price']['total']),
                    'price_currency': offer['price']['currency'],
                    'duration': itinerary['duration'],
                    'stops': len(segments) - 1,
                    'booking_class': first_segment.get('cabin', 'N/A'),
                    'seats_available': first_segment.get('numberOfBookableSeats', 0),
                    'collected_at': datetime.now().isoformat()
                }
                parsed_flights.append(flight_data)
            except (KeyError, IndexError, ValueError) as e:
                logger.warning(f"Error parsing flight offer: {e}")
                continue
        return parsed_flights
    
    def collect_flight_data(self, start_date: Optional[str] = None):
        start_dt = datetime.strptime('2025-08-01', '%Y-%m-%d')
        logger.info(f"Starting flight data collection for 32 days from 2025-08-01 to 2025-09-01")
        for route in self.routes:
            logger.info(f"Collecting data for route: {route['route_name']}")
            for day_offset in range(32):
                current_date = start_dt + timedelta(days=day_offset)
                date_str = current_date.strftime('%Y-%m-%d')
                logger.info(f"Searching flights for {route['origin']} to {route['destination']} on {date_str}")
                flight_offers = self.search_flights(route['origin'], route['destination'], date_str)
                if flight_offers:
                    parsed_flights = self.parse_flight_data(
                        flight_offers, route['route_name'], route['origin'], route['destination']
                    )
                    self.collected_flights.extend(parsed_flights)
                    logger.info(f"Collected {len(parsed_flights)} flights for {date_str}")
                time.sleep(1)
            logger.info(f"Route {route['route_name']}: {len([f for f in self.collected_flights if f['route_name'] == route['route_name']])} flights collected")
            time.sleep(2)
        logger.info(f"Data collection completed. Total flights collected: {len(self.collected_flights)}")
    
    def get_statistics(self):
        if not self.collected_flights:
            print("No flight data to display statistics for.")
            return
        
        df = pd.DataFrame(self.collected_flights)
        
        route_stats = df.groupby(['route_name', 'price_currency']).agg({
            'price_amount': ['count', 'min', 'max', 'mean']
        }).round(2)
        
        airline_stats = df.groupby('airline_name').agg({
            'price_amount': ['count', 'mean']
        }).round(2).sort_values(('price_amount', 'count'), ascending=False).head(10)
        
        print("\n=== FLIGHT DATA STATISTICS ===")
        print(f"\nTotal flights collected: {len(self.collected_flights)}")
        print("\n=== FLIGHTS BY ROUTE ===")
        print(route_stats)
        print("\n=== TOP AIRLINES BY FLIGHT COUNT ===")
        print(airline_stats)
    
    def export_to_csv(self, filename: str = "flight_data_export.csv"):
        if not self.collected_flights:
            print("No flight data to export.")
            return None
        
        df = pd.DataFrame(self.collected_flights)
        df = df.sort_values(['departure_date', 'route_name'])
        df.to_csv(filename, index=False)
        logger.info(f"Flight data exported to {filename}")

        return filename

def export_to_sql(filename):
    df = pd.read_csv(filename)
    conn = sqlite3.connect("database.db")
    df.to_sql("flight_data_sql", conn, if_exists="replace", index=False)
    conn.close()

def main():
    try:
        collector = FlightDataCollector()
        
        print("=== HUVTSP ROVE Flight Data Collector ===")
        print("This script will collect flight data from Amadeus API for predefined routes.")
        print("\nRoutes to be searched:")
        for i, route in enumerate(collector.routes, 1):
            print(f"{i}. {route['route_name']} ({route['origin']} → {route['destination']})")
        
        response = input(f"\nDo you want to start collecting flight data for the next 32 days? (y/n): ")
        
        if response.lower() in ['y', 'yes']:
            collector.collect_flight_data()
            collector.get_statistics()
            csv_file = collector.export_to_csv()
            if csv_file:
                export_to_sql(csv_file)
                print(f"\nData has been exported to: {csv_file}")
            print("\nData has been exported to SQL file.")
            
        else:
            print("Data collection cancelled.")
            if collector.collected_flights:
                collector.get_statistics()
            else:
                print("No existing flight data found.")
    
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print("\nPlease make sure you have set up your Amadeus API credentials in the .env file:")
        print("1. Copy your API key and secret from Amadeus for Developers")
        print("2. Replace 'your_amadeus_api_key_here' and 'your_amadeus_api_secret_here' in .env file")
    
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        print(f"An error occurred: {e}")

if __name__ == "__main__":

    main()
