import os
import sqlite3
import pandas as pd
from datetime import datetime
from typing import List, Dict, Tuple
from amadeus import Client, ResponseError
from dotenv import load_dotenv

load_dotenv()

class RedemptionOptimizer:
    def __init__(self):
        api_key = os.getenv('AMADEUS_API_KEY')
        api_secret = os.getenv('AMADEUS_API_SECRET')
        # Initialize Amadeus client only if credentials are present
        self.amadeus = None
        try:
            if api_key and api_secret:
                self.amadeus = Client(client_id=api_key, client_secret=api_secret)
        except Exception:
            # In case the client cannot be created, fall back to mock mode
            self.amadeus = None

        # Track whether mock data was used in the last call
        self.last_used_mock_flights = False
        
        self.award_charts = {
            'domestic': {'economy': 12500, 'business': 25000, 'first': 50000},
            'international': {'economy': 30000, 'business': 60000, 'first': 100000},
            'short_haul': {'economy': 7500, 'business': 15000, 'first': 25000}
        }
        
        # Hotel redemption rates (cents per mile)
        self.hotel_redemption_rates = {
            'economy': 1.45,  # 1.45 cents per mile for economy hotels
            'mid_scale': 1.65,  # 1.65 cents per mile for mid-scale hotels
            'upscale': 1.95,  # 1.95 cents per mile for upscale hotels
            'luxury': 2.25   # 2.25 cents per mile for luxury hotels
        }
        
        self.gift_card_rates = {
            'giftcards.com': 4, 'visa gift card': 4, 'mastercard gift card': 4, 'airbnb gift card': 4,
            'doordash gift card': 4, 'uber gift card': 4, 'uber eats gift card': 4, 'starbucks gift card': 4,
            'target gift card': 1.3, 'cvs gift card': 4, 'giant eagle gift card': 4, 'fanatics gift card': 4,
            'melting pot gift card': 4, 'thirdlove gift card': 4, 'tops friendly markets gift card': 4,
            'jtv gift card': 4, 'zappos gift card': 4, "claire's gift card": 4, "famous dave's gift card": 4,
            'on the border gift card': 4, 'circle k gift card': 4, "fazoli's gift card": 4,
            'boxlunch gift card': 4, 'bonefish grill gift card': 4, "mcdonald's gift card": 4,
            'turo gift card': 4, 'golfnow gift card': 4, 'chewy gift card': 4, 'siriusxm gift card': 4,
            'l.l. bean gift card': 4, 'carnival cruises gift card': 0.6, 'best buy gift card': 0.6,
            'alamo drafthouse cinemas gift card': 4, 'quince gift card': 4, "mcalister's deli gift card": 4,
            'emagine theaters gift card': 4, "friendly's gift card": 4, "cheddar's scratch kitchen gift card": 4,
            'dazn gift card': 4, "dave & buster's gift card": 4, "ruth's chris steak house gift card": 4,
            'fogo de chao gift card': 4, "morton's steakhouse gift card": 4, 'pacsun gift card': 4,
            'the container store gift card': 4, 'uno pizzeria & grill gift card': 4, "bj's restaurants gift card": 4,
            "logan's roadhouse gift card": 4, 'bob evans gift card': 4, 'lorna jane gift card': 4,
            'lane bryant gift card': 4, 'guess gift card': 4, 'shutterfly gift card': 4,
            'bubba gump gift card': 4, 'ace hardware gift card': 4, 'quiznos gift card': 4,
            'thredup gift card': 4, 'hopper gift card': 4, 'tommy bahama gift card': 4,
            "carrabba's italian grill gift card": 4, 'sweetfrog gift card': 4, 'qdoba gift card': 4,
            "dick's sporting goods gift card": 1.3, 'american airlines gift card': 1.3,
            "dunkin' gift card": 1.3, 'zara gift card': 1.3, 'apple gift card': 1.3, 'nike gift card': 0.6,
            'chuck e. cheese gift card': 4, 'pandora gift card': 4, "bloomingdale's gift card": 4,
            'belk gift card': 4, 'athleta gift card': 4, 'barnes & noble gift card': 4,
            'virgin experience gifts gift card': 4, 'jcpenney gift card': 4, 'spafinder gift card': 4,
            'build-a-bear gift card': 4, 'california pizza kitchen gift card': 4, 'ruby tuesday gift card': 4,
            'smoothie king gift card': 4, 'old navy gift card': 4, 'aerie gift card': 4,
            'advance auto parts gift card': 4, 'tillys gift card': 4, 'guitar center gift card': 4,
            'vudu gift card': 4, 'topgolf gift card': 4, 'the coffee bean & tea leaf gift card': 4,
            'white house black market gift card': 4, 'wawa gift card': 4, 'dollar shave club gift card': 4,
            'untuckit gift card': 4, 'torrid gift card': 4, 'pep boys gift card': 4,
            'famous footwear gift card': 4, 'jiffy lube gift card': 4, 'cold stone creamery gift card': 4,
            'sling tv gift card': 4, 'buffalo wild wings gift card': 4, "auntie anne's gift card": 4,
            'cinnabon gift card': 4, 'kfc gift card': 4, "bass pro shops / cabela's gift card": 4,
            'gap gift card': 4, 'hotels.com gift card': 4, 'disney gift card': 4, 'american girl gift card': 4,
            "carter's / oshkosh b'gosh gift card": 4, 'eddie bauer gift card': 4, "chico's gift card": 4,
            'poshmark gift card': 4, 'oura ring gift card': 4, 'american eagle gift card': 4,
            'aeropostale gift card': 4, 'hollister gift card': 4, 'abercrombie & fitch gift card': 4,
            'twitch gift card': 4, 'crutchfield gift card': 4, 'lulus gift card': 4, "lands' end gift card": 4,
            'michaels gift card': 4, "kirkland's gift card": 4, 'h&m gift card': 4, 'hulu gift card': 4,
            'meijer gift card': 4, 'crate & barrel gift card': 4, 'firebirds wood fired grill gift card': 4,
            'red robin gift card': 4, 'ihop gift card': 4, 'krispy kreme gift card': 4,
            'outback steakhouse gift card': 4, 'olive garden gift card': 4, 'speedway gift card': 4,
            'shell gift card': 4, 'sonic drive-in gift card': 4, 'texas roadhouse gift card': 4,
            'subway gift card': 4, 'red lobster gift card': 4, 'papa johns gift card': 4,
            'panda express gift card': 4, 'meta quest gift card': 4, "macy's gift card": 4,
            "jersey mike's gift card": 4, 'taco bell gift card': 4, 'five guys gift card': 4,
            "chili's gift card": 4, 'burger king gift card': 4, 'rei gift card': 4, 'marshalls gift card': 4,
            'homegoods gift card': 4, 'lego gift card': 4, 'gamestop gift card': 4,
            'academy sports + outdoors gift card': 4, 'roblox gift card': 4, 'nordstrom gift card': 4,
            'chipotle gift card': 4, 'the home depot gift card': 4, 'wayfair gift card': 4,
            "victoria's secret gift card": 4, 'tire discounters gift card': 4, 'dsw gift card': 4,
            'stop & shop gift card': 4, 'nintendo eshop gift card': 4, 'the cheesecake factory gift card': 4,
            'nordstrom rack gift card': 4, 'petsmart gift card': 4, 'tj maxx gift card': 4,
            'lululemon gift card': 4, 'spotify gift card': 4, 'lyft gift card': 4, "domino's gift card": 4,
            'southwest airlines gift card': 4, 'sony playstation gift card': 4, 'microsoft xbox gift card': 4,
            'autozone gift card': 4, 'saks off 5th gift card': 4, 'adidas gift card': 4,
            'ulta beauty gift card': 4, 'bath & body works gift card': 4, 'amtrak gift card': 4,
            'petco gift card': 4, 'saks fifth avenue gift card': 4, 'total wine & more gift card': 4,
            'instacart gift card': 4, 'google play gift card': 4, 'regal cinemas gift card': 4,
            'bp amoco gift card': 4, 'grubhub gift card': 4, 'panera bread gift card': 4,
            "kohl's gift card": 4, 'cinemark gift card': 4, 'delta air lines gift card': 4,
            'netflix gift card': 4, 'ikea gift card': 4, 'fandango gift card': 4, "lowe's gift card": 4,
            'sephora gift card': 4, "applebee's gift card": 4, 'amc theatres gift card': 4,
            'gift card outlets': 0.9
        }
    
    def gather_flight_data(self, origin: str, destination: str, departure_date: str) -> List[Dict]:
        """Return flight offers. Falls back to mock data when API is unavailable/errors."""
        # Default to not using mock until proven otherwise
        self.last_used_mock_flights = False

        # Try live API when available
        if self.amadeus is not None:
            try:
                response = self.amadeus.shopping.flight_offers_search.get(
                    originLocationCode=origin,
                    destinationLocationCode=destination,
                    departureDate=departure_date,
                    adults=1,
                    max=10
                )

                flights = []
                for offer in response.data:
                    flight = {
                        'price': float(offer['price']['total']),
                        'currency': offer['price']['currency'],
                        'airline': offer['itineraries'][0]['segments'][0]['carrierCode'],
                        'duration': offer['itineraries'][0]['duration'],
                        'cabin': offer['travelerPricings'][0]['fareDetailsBySegment'][0].get('cabin', 'ECONOMY')
                    }
                    flights.append(flight)

                if flights:
                    return flights
            except Exception as e:
                print(f"Error gathering flight data: {e}")

        # Fallback to mock data so the UI still shows results
        self.last_used_mock_flights = True
        return self._mock_flight_offers(origin, destination)

    def _mock_flight_offers(self, origin: str, destination: str) -> List[Dict]:
        """Provide deterministic mock flight data to keep the app usable offline."""
        # Reasonable sample prices and cabins to generate varied CPMs
        sample_offers = [
            {"price": 189.0, "currency": "USD", "airline": "DL", "duration": "PT6H10M", "cabin": "ECONOMY"},
            {"price": 249.0, "currency": "USD", "airline": "AA", "duration": "PT6H05M", "cabin": "ECONOMY"},
            {"price": 512.0, "currency": "USD", "airline": "UA", "duration": "PT6H00M", "cabin": "BUSINESS"},
            {"price": 799.0, "currency": "USD", "airline": "B6", "duration": "PT5H55M", "cabin": "FIRST"},
            {"price": 329.0, "currency": "USD", "airline": "AS", "duration": "PT6H20M", "cabin": "ECONOMY"},
        ]
        flights = []
        for offer in sample_offers:
            flights.append({
                'price': float(offer['price']),
                'currency': offer['currency'],
                'airline': offer['airline'],
                'duration': offer['duration'],
                'cabin': offer['cabin']
            })
        return flights
    
    def gather_hotel_data(self, city_code: str, check_in_date: str, check_out_date: str) -> List[Dict]:
        """Gather hotel data from Amadeus API"""
        try:
            # Get hotels in the city
            hotels_response = self.amadeus.reference_data.locations.hotels.by_city.get(
                cityCode=city_code
            )
            
            if not hotels_response.data:
                return []
            
            hotels = []
            hotels_checked = 0
            
            for hotel in hotels_response.data[:10]:  # Check first 10 hotels
                try:
                    hotel_id = hotel.get('hotelId')
                    if hotel_id:
                        offers_response = self.amadeus.shopping.hotel_offers_search.get(
                            hotelIds=hotel_id,
                            checkInDate=check_in_date,
                            checkOutDate=check_out_date,
                            adults=1
                        )
                        
                        if offers_response.data:
                            for offer in offers_response.data:
                                hotel_info = offer.get('hotel', {})
                                first_offer = offer.get('offers', [{}])[0]
                                price = first_offer.get('price', {})
                                
                                # Determine hotel category based on rating
                                rating = hotel_info.get('rating', 0)
                                if rating >= 4.5:
                                    category = 'luxury'
                                elif rating >= 4.0:
                                    category = 'upscale'
                                elif rating >= 3.0:
                                    category = 'mid_scale'
                                else:
                                    category = 'economy'
                                
                                hotel_data = {
                                    'name': hotel_info.get('name', 'Unknown'),
                                    'price': float(price.get('total', 0)),
                                    'currency': price.get('currency', 'USD'),
                                    'rating': rating,
                                    'category': category,
                                    'chain': hotel_info.get('chainCode', 'Independent')
                                }
                                hotels.append(hotel_data)
                                hotels_checked += 1
                                
                                if hotels_checked >= 20:  # Limit to 20 hotels
                                    break
                        
                        if hotels_checked >= 20:
                            break
                            
                except Exception as e:
                    continue
            
            return hotels
            
        except Exception as e:
            print(f"Error gathering hotel data: {e}")
            return []
    
    def get_city_code(self, city_name: str) -> str:
        """Get the IATA city code for a given city name"""
        try:
            response = self.amadeus.reference_data.locations.get(
                keyword=city_name,
                subType="CITY"
            )
            if response.data:
                return response.data[0]['iataCode']
            return None
        except Exception as e:
            print(f"Error getting city code for {city_name}: {e}")
            return None
    
    def calculate_route_type(self, origin: str, destination: str) -> str:
        us_airports = ['JFK', 'LAX', 'ORD', 'DFW', 'ATL', 'SFO', 'BOS', 'SEA', 'DCA', 'IAD']
        eu_airports = ['LHR', 'CDG', 'FRA', 'MAD', 'BCN', 'FCO', 'AMS', 'MUC']
        
        if origin in us_airports and destination in us_airports:
            if origin in ['JFK', 'BOS'] and destination in ['DCA', 'IAD']:
                return 'short_haul'
            return 'domestic'
        elif (origin in us_airports and destination not in us_airports) or \
             (origin not in us_airports and destination in us_airports):
            return 'international'
        else:
            return 'short_haul'
    
    def calculate_value_per_mile(self, cash_price: float, miles_required: int) -> float:
        if miles_required == 0:
            return 0
        return (cash_price / miles_required) * 100
    
    def get_award_miles_required(self, origin: str, destination: str, cabin_class: str) -> int:
        route_type = self.calculate_route_type(origin, destination)
        cabin = cabin_class.lower() if cabin_class else 'economy'
        
        if cabin in ['premium_economy', 'premium']:
            cabin = 'economy'
        elif cabin in ['business', 'first']:
            cabin = cabin
        else:
            cabin = 'economy'
            
        return self.award_charts[route_type][cabin]
    
    def analyze_flight_redemptions(self, user_miles: int, origin: str, 
                                  destination: str, departure_date: str) -> List[Dict]:
        flights = self.gather_flight_data(origin, destination, departure_date)
        redemption_options = []
        
        for flight in flights:
            miles_required = self.get_award_miles_required(origin, destination, flight['cabin'])
            
            if miles_required <= user_miles:
                cpm = self.calculate_value_per_mile(flight['price'], miles_required)
                
                redemption_options.append({
                    'type': 'flight',
                    'description': f"{flight['airline']} {flight['cabin']} class",
                    'cash_value': flight['price'],
                    'miles_required': miles_required,
                    'cpm': cpm,
                    'details': {
                        'origin': origin,
                        'destination': destination,
                        'date': departure_date,
                        'duration': flight['duration'],
                        'airline': flight['airline'],
                        'cabin': flight['cabin']
                    }
                })
        
        return redemption_options
    
    def analyze_hotel_redemptions(self, user_miles: int, city_name: str, 
                                 check_in_date: str, check_out_date: str) -> List[Dict]:
        """Analyze hotel redemption options"""
        city_code = self.get_city_code(city_name)
        if not city_code:
            return []
        
        hotels = self.gather_hotel_data(city_code, check_in_date, check_out_date)
        redemption_options = []
        
        for hotel in hotels:
            # Calculate miles required based on hotel category (cents per mile)
            cpm_rate = self.hotel_redemption_rates[hotel['category']]
            # For hotels: miles = price / (cpm_rate / 100)
            miles_required = int(hotel['price'] / (cpm_rate / 100))
            
            if miles_required <= user_miles:
                cpm = cpm_rate  # Use the fixed CPM rate for hotels
                
                redemption_options.append({
                    'type': 'hotel',
                    'description': f"{hotel['name']} ({hotel['category'].replace('_', ' ').title()})",
                    'cash_value': hotel['price'],
                    'miles_required': miles_required,
                    'cpm': cpm,
                    'details': {
                        'hotel_name': hotel['name'],
                        'category': hotel['category'],
                        'rating': hotel['rating'],
                        'chain': hotel['chain'],
                        'check_in': check_in_date,
                        'check_out': check_out_date,
                        'city': city_name
                    }
                })
        
        return redemption_options
    
    def analyze_gift_card_redemptions(self, user_miles: int) -> List[Dict]:
        redemption_options = []
        
        for brand, miles_per_dollar in self.gift_card_rates.items():
            max_value = user_miles / miles_per_dollar
            if max_value >= 25:
                cpm = self.calculate_value_per_mile(max_value, user_miles)
                
                redemption_options.append({
                    'type': 'gift_card',
                    'description': f"{brand.title()}",
                    'cash_value': max_value,
                    'miles_required': user_miles,
                    'cpm': cpm,
                    'details': {
                        'brand': brand.title(),
                        'miles_per_dollar': miles_per_dollar,
                        'max_amount': f"${max_value:.2f}"
                    }
                })
        
        return redemption_options
    
    def optimize_redemption(self, user_miles: int, origin: str = None, 
                           destination: str = None, departure_date: str = None,
                           city_name: str = None, check_in_date: str = None, 
                           check_out_date: str = None) -> Dict:
        all_options = []
        flight_options = []
        hotel_options = []
        gift_card_options = []
        
        # Analyze flights if flight parameters are provided
        if origin and destination and departure_date:
            flight_options = self.analyze_flight_redemptions(
                user_miles, origin, destination, departure_date
            )
            all_options.extend(flight_options)
        
        # Analyze hotels if hotel parameters are provided
        if city_name and check_in_date and check_out_date:
            hotel_options = self.analyze_hotel_redemptions(
                user_miles, city_name, check_in_date, check_out_date
            )
            all_options.extend(hotel_options)
        
        # Always analyze gift cards
        gift_card_options = self.analyze_gift_card_redemptions(user_miles)
        all_options.extend(gift_card_options)
        
        # Sort each category by CPM and get top 3 for each
        flight_options.sort(key=lambda x: x['cpm'], reverse=True)
        hotel_options.sort(key=lambda x: x['cpm'], reverse=True)
        gift_card_options.sort(key=lambda x: x['cpm'], reverse=True)
        
        top_flights = flight_options[:3]
        top_hotels = hotel_options[:3]
        top_gift_cards = gift_card_options[:3]
        
        # Find overall best option
        all_options.sort(key=lambda x: x['cpm'], reverse=True)
        best_overall = all_options[0] if all_options else None
        
        output = {
            'user_input': {
                'miles_balance': user_miles,
                'origin': origin,
                'destination': destination,
                'travel_date': departure_date,
                'city_name': city_name,
                'check_in_date': check_in_date,
                'check_out_date': check_out_date
            },
            'best_overall_recommendation': best_overall,
            'top_options_by_category': {
                'flights': top_flights,
                'hotels': top_hotels,
                'gift_cards': top_gift_cards
            },
            'summary': self._generate_summary(best_overall, user_miles),
            'detailed_analysis': {
                'total_options_analyzed': len(all_options),
                'flight_options': len(flight_options),
                'hotel_options': len(hotel_options),
                'gift_card_options': len(gift_card_options),
                'average_cpm': sum(opt['cpm'] for opt in all_options) / len(all_options) if all_options else 0
            }
        }
        
        return output
    
    def _generate_summary(self, best_option: Dict, user_miles: int) -> str:
        if not best_option:
            return f"No redemption options available for {user_miles:,} miles."
        
        if best_option['type'] == 'flight':
            return (f"BEST OVERALL VALUE: Redeem {best_option['miles_required']:,} miles for a "
                   f"{best_option['description']} flight worth ${best_option['cash_value']:.2f}. "
                   f"This gives you {best_option['cpm']:.2f} cents per mile in value.")
        elif best_option['type'] == 'hotel':
            return (f"BEST OVERALL VALUE: Redeem {best_option['miles_required']:,} miles for a "
                   f"{best_option['description']} hotel stay worth ${best_option['cash_value']:.2f}. "
                   f"This gives you {best_option['cpm']:.2f} cents per mile in value.")
        else:
            return (f"BEST OVERALL VALUE: Redeem your {user_miles:,} miles for a "
                   f"{best_option['description']} worth ${best_option['cash_value']:.2f}. "
                   f"This gives you {best_option['cpm']:.2f} cents per mile in value.")

def main():
    print("=== ROVE MILES REDEMPTION OPTIMIZER ===\n")
    
    user_miles = int(input("Enter number of miles: "))
    
    # Flight search
    use_flight = input("Do you want to search for flights? (y/n): ").lower() == 'y'
    origin = destination = departure_date = None
    if use_flight:
        origin = input("Enter origin (e.g., JFK): ").upper()
        destination = input("Enter destination (e.g., LAX): ").upper()
        departure_date = input("Enter departure date (YYYY-MM-DD): ")
    
    # Hotel search
    use_hotel = input("Do you want to search for hotels? (y/n): ").lower() == 'y'
    city_name = check_in_date = check_out_date = None
    if use_hotel:
        city_name = input("Enter city name (e.g., Madrid, Barcelona): ").strip()
        check_in_date = input("Enter check-in date (YYYY-MM-DD): ")
        check_out_date = input("Enter check-out date (YYYY-MM-DD): ")
    
    optimizer = RedemptionOptimizer()
    
    print("\nAnalyzing redemption options...")
    result = optimizer.optimize_redemption(
        user_miles, origin, destination, departure_date, 
        city_name, check_in_date, check_out_date
    )
    
    print("\n" + "="*60)
    print("OPTIMIZATION RESULTS")
    print("="*60)
    
    print(f"\nYour miles: {result['user_input']['miles_balance']:,}")
    if result['user_input']['origin']:
        print(f"Flight Route: {result['user_input']['origin']} → {result['user_input']['destination']}")
        print(f"Flight Date: {result['user_input']['travel_date']}")
    if result['user_input']['city_name']:
        print(f"Hotel City: {result['user_input']['city_name']}")
        print(f"Hotel Dates: {result['user_input']['check_in_date']} to {result['user_input']['check_out_date']}")
    
    print(f"\n{result['summary']}")
    
    # Display top options by category
    print("\n" + "="*60)
    print("TOP 3 OPTIONS BY CATEGORY")
    print("="*60)
    
    # Flights
    if result['top_options_by_category']['flights']:
        print(f"\n🛫 TOP 3 FLIGHT OPTIONS:")
        for i, option in enumerate(result['top_options_by_category']['flights'], 1):
            print(f"\n{i}. {option['description']}")
            print(f"   Value: ${option['cash_value']:.2f}")
            print(f"   Miles: {option['miles_required']:,}")
            print(f"   CPM: {option['cpm']:.2f} cents/mile")
            if 'details' in option and 'duration' in option['details']:
                print(f"   Duration: {option['details']['duration']}")
    else:
        print(f"\n🛫 FLIGHT OPTIONS: No flight options available")
    
    # Hotels
    if result['top_options_by_category']['hotels']:
        print(f"\n🏨 TOP 3 HOTEL OPTIONS:")
        for i, option in enumerate(result['top_options_by_category']['hotels'], 1):
            print(f"\n{i}. {option['description']}")
            print(f"   Value: ${option['cash_value']:.2f}")
            print(f"   Miles: {option['miles_required']:,}")
            print(f"   CPM: {option['cpm']:.2f} cents/mile")
            if 'details' in option and 'rating' in option['details']:
                print(f"   Rating: {option['details']['rating']}")
    else:
        print(f"\n🏨 HOTEL OPTIONS: No hotel options available")
    
    # Gift Cards
    if result['top_options_by_category']['gift_cards']:
        print(f"\n🎁 TOP 3 GIFT CARD OPTIONS:")
        for i, option in enumerate(result['top_options_by_category']['gift_cards'], 1):
            print(f"\n{i}. {option['description']}")
            print(f"   Value: ${option['cash_value']:.2f}")
            print(f"   Miles: {option['miles_required']:,}")
            print(f"   CPM: {option['cpm']:.2f} cents/mile")
            if 'details' in option and 'miles_per_dollar' in option['details']:
                print(f"   Miles per Dollar: {option['details']['miles_per_dollar']}")
    else:
        print(f"\n🎁 GIFT CARD OPTIONS: No gift card options available")
    
    print("\n" + "="*60)
    print("ANALYSIS SUMMARY")
    print("="*60)
    print(f"Total options analyzed: {result['detailed_analysis']['total_options_analyzed']}")
    print(f"Flight options: {result['detailed_analysis']['flight_options']}")
    print(f"Hotel options: {result['detailed_analysis']['hotel_options']}")
    print(f"Gift card options: {result['detailed_analysis']['gift_card_options']}")
    print(f"Average CPM: {result['detailed_analysis']['average_cpm']:.2f} cents/mile")

if __name__ == "__main__":
    main()