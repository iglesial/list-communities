from pathlib import Path
import json
from icalendar import Calendar, Event
from datetime import datetime
from typing import List, Dict

class ICalendarGenerator:
    """Generates iCal files from JSON event data"""
    
    @staticmethod
    def create_calendar(name: str, description: str = "") -> Calendar:
        """Create a new iCalendar object with basic metadata"""
        cal = Calendar()
        cal.add('prodid', f'-//{name}//Bordeaux Community Events//FR')
        cal.add('version', '2.0')
        cal.add('x-wr-calname', name)
        if description:
            cal.add('x-wr-caldesc', description)
        return cal

    @staticmethod
    def create_event_from_json(event_data: Dict) -> Event:
        """Convert a JSON event entry to an iCal event"""
        event = Event()
        
        # Required fields
        event.add('summary', event_data['title'])
        event.add('dtstart', datetime.fromisoformat(event_data['date']))
        
        # Add URL both as a property and in description
        event.add('url', event_data['url'])
        description_parts = [f"🔗 {event_data['url']}"]
        
        # Add venue/location information if available
        location = None
        if 'venue' in event_data:
            venue = event_data['venue']
            location = f"{venue['name']}, {venue['address']}, {venue['city']}, {venue['country']}"
        elif 'location' in event_data:
            location = event_data['location']
            
        if location:
            event.add('location', location)
            description_parts.append(f"📍 {location}")
        
        # Add description if available
        if 'description' in event_data:
            description_parts.append("\n" + event_data['description'])
        
        # Add community attribution
        description_parts.append(f"\nCommunauté: {event_data['community']}")
        
        # Add online/offline status
        if event_data.get('is_online'):
            description_parts.append("💻 Événement en ligne")
        
        # Add RSVP information if available
        if 'rsvp_count' in event_data:
            description_parts.append(f"👥 {event_data['rsvp_count']} participant(s)")
        if 'rsvp_limit' in event_data:
            description_parts.append(f"Limité à {event_data['rsvp_limit']} places")
        
        # Combine all description parts
        event.add('description', "\n".join(description_parts))
        event.add('uid', f"{event_data['url']}@community-events")
        
        return event

    def process_community_folder(self, folder_path: Path, global_calendar: Calendar) -> None:
        """Process a community folder and create its calendar"""
        events_file = folder_path / 'events.json'
        if not events_file.exists():
            return
            
        # Read events
        try:
            with open(events_file, 'r', encoding='utf-8') as f:
                events_data = json.load(f)
        except Exception as e:
            print(f"Error reading events file {events_file}: {e}")
            return
            
        # Create community calendar
        community_name = folder_path.name
        community_cal = self.create_calendar(
            f"Événements {community_name}",
            f"Calendrier des événements de la communauté {community_name}"
        )
        
        # Process each event
        for event_data in events_data:
            try:
                ical_event = self.create_event_from_json(event_data)
                community_cal.add_component(ical_event)
                global_calendar.add_component(ical_event)
            except Exception as e:
                print(f"Error processing event {event_data.get('title', 'Unknown')}: {e}")
                continue
        
        # Write community calendar
        output_path = folder_path / 'events.ics'
        try:
            with open(output_path, 'wb') as f:
                f.write(community_cal.to_ical())
            print(f"Created calendar for {community_name}")
        except Exception as e:
            print(f"Error writing calendar file for {community_name}: {e}")

    def generate_calendars(self, root_dir: Path):
        """Generate iCal files for each community and a global calendar"""
        # Create global calendar
        global_cal = self.create_calendar(
            "Tous les événements communautaires",
            "Calendrier global de tous les événements communautaires"
        )
        
        # Process each community folder
        for item in root_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                self.process_community_folder(item, global_cal)
        
        # Write global calendar
        try:
            with open(root_dir / 'events.ics', 'wb') as f:
                f.write(global_cal.to_ical())
            print("Created global calendar")
        except Exception as e:
            print(f"Error writing global calendar: {e}")

def main():
    """Main script execution"""
    root_dir = Path('.')
    generator = ICalendarGenerator()
    generator.generate_calendars(root_dir)

if __name__ == "__main__":
    main()
