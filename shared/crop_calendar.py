"""
Crop Calendar Database for Indian Farmers
Planting, harvesting, and care schedules for major crops
"""

from typing import Dict, List, Optional


class CropCalendar:
    """Crop calendar with planting and harvesting schedules"""
    
    def __init__(self):
        """Initialize crop calendar database"""
        self.crops = self._load_crop_data()
        self.regions = ["North India", "South India", "East India", "West India", "Central India"]
    
    def _load_crop_data(self) -> Dict:
        """Load crop calendar data"""
        return {
            "Wheat": {
                "North India": {
                    "planting": "October - November",
                    "harvesting": "March - April",
                    "duration": "120-150 days",
                    "fertilizer_schedule": [
                        {"time": "At sowing", "type": "DAP + Urea", "amount": "100 kg/acre"},
                        {"time": "21 days after sowing", "type": "Urea", "amount": "50 kg/acre"},
                        {"time": "40 days after sowing", "type": "Urea", "amount": "50 kg/acre"}
                    ],
                    "irrigation": "4-6 irrigations required",
                    "pest_control": [
                        {"time": "30 days", "issue": "Aphids", "treatment": "Spray insecticide"},
                        {"time": "60 days", "issue": "Rust", "treatment": "Fungicide spray"}
                    ]
                },
                "Central India": {
                    "planting": "November - December",
                    "harvesting": "March - April",
                    "duration": "110-130 days",
                    "fertilizer_schedule": [
                        {"time": "At sowing", "type": "NPK", "amount": "80 kg/acre"},
                        {"time": "25 days", "type": "Urea", "amount": "40 kg/acre"}
                    ],
                    "irrigation": "3-5 irrigations",
                    "pest_control": [
                        {"time": "35 days", "issue": "Termites", "treatment": "Soil treatment"}
                    ]
                }
            },
            "Rice": {
                "North India": {
                    "planting": "June - July (Kharif)",
                    "harvesting": "October - November",
                    "duration": "120-140 days",
                    "fertilizer_schedule": [
                        {"time": "At transplanting", "type": "DAP", "amount": "50 kg/acre"},
                        {"time": "20 days", "type": "Urea", "amount": "40 kg/acre"},
                        {"time": "40 days", "type": "Urea + Potash", "amount": "40 kg/acre"}
                    ],
                    "irrigation": "Standing water required",
                    "pest_control": [
                        {"time": "30 days", "issue": "Stem borer", "treatment": "Carbofuran"},
                        {"time": "60 days", "issue": "Leaf folder", "treatment": "Spray pesticide"}
                    ]
                },
                "South India": {
                    "planting": "June - July (Kharif), January (Rabi)",
                    "harvesting": "October - November, April - May",
                    "duration": "110-130 days",
                    "fertilizer_schedule": [
                        {"time": "At transplanting", "type": "NPK", "amount": "60 kg/acre"},
                        {"time": "25 days", "type": "Urea", "amount": "35 kg/acre"}
                    ],
                    "irrigation": "Continuous flooding",
                    "pest_control": [
                        {"time": "40 days", "issue": "Brown plant hopper", "treatment": "Systemic insecticide"}
                    ]
                }
            },
            "Cotton": {
                "North India": {
                    "planting": "April - May",
                    "harvesting": "October - December",
                    "duration": "150-180 days",
                    "fertilizer_schedule": [
                        {"time": "At sowing", "type": "DAP", "amount": "50 kg/acre"},
                        {"time": "30 days", "type": "Urea", "amount": "40 kg/acre"},
                        {"time": "60 days", "type": "Urea + Potash", "amount": "40 kg/acre"}
                    ],
                    "irrigation": "5-7 irrigations",
                    "pest_control": [
                        {"time": "45 days", "issue": "Bollworm", "treatment": "Bt spray"},
                        {"time": "75 days", "issue": "Whitefly", "treatment": "Neem oil spray"}
                    ]
                },
                "Central India": {
                    "planting": "May - June",
                    "harvesting": "November - January",
                    "duration": "160-190 days",
                    "fertilizer_schedule": [
                        {"time": "At sowing", "type": "NPK", "amount": "60 kg/acre"},
                        {"time": "35 days", "type": "Urea", "amount": "45 kg/acre"}
                    ],
                    "irrigation": "6-8 irrigations",
                    "pest_control": [
                        {"time": "50 days", "issue": "Pink bollworm", "treatment": "Pheromone traps"}
                    ]
                }
            },
            "Maize": {
                "North India": {
                    "planting": "June - July (Kharif), February (Rabi)",
                    "harvesting": "September - October, May - June",
                    "duration": "80-110 days",
                    "fertilizer_schedule": [
                        {"time": "At sowing", "type": "DAP", "amount": "40 kg/acre"},
                        {"time": "25 days", "type": "Urea", "amount": "50 kg/acre"}
                    ],
                    "irrigation": "3-4 irrigations",
                    "pest_control": [
                        {"time": "30 days", "issue": "Fall armyworm", "treatment": "Spray insecticide"},
                        {"time": "50 days", "issue": "Stem borer", "treatment": "Granular insecticide"}
                    ]
                },
                "South India": {
                    "planting": "June - July, October - November",
                    "harvesting": "September - October, January - February",
                    "duration": "75-100 days",
                    "fertilizer_schedule": [
                        {"time": "At sowing", "type": "NPK", "amount": "45 kg/acre"},
                        {"time": "20 days", "type": "Urea", "amount": "40 kg/acre"}
                    ],
                    "irrigation": "2-3 irrigations",
                    "pest_control": [
                        {"time": "35 days", "issue": "Shoot fly", "treatment": "Seed treatment"}
                    ]
                }
            },
            "Sugarcane": {
                "North India": {
                    "planting": "February - March (Spring), October (Autumn)",
                    "harvesting": "December - March (12-14 months)",
                    "duration": "12-14 months",
                    "fertilizer_schedule": [
                        {"time": "At planting", "type": "FYM", "amount": "10 tons/acre"},
                        {"time": "30 days", "type": "Urea + DAP", "amount": "100 kg/acre"},
                        {"time": "60 days", "type": "Urea", "amount": "80 kg/acre"},
                        {"time": "90 days", "type": "Potash", "amount": "40 kg/acre"}
                    ],
                    "irrigation": "10-12 irrigations",
                    "pest_control": [
                        {"time": "60 days", "issue": "Early shoot borer", "treatment": "Carbofuran"},
                        {"time": "120 days", "issue": "Top borer", "treatment": "Spray insecticide"}
                    ]
                }
            },
            "Potato": {
                "North India": {
                    "planting": "October - November",
                    "harvesting": "January - February",
                    "duration": "90-120 days",
                    "fertilizer_schedule": [
                        {"time": "At planting", "type": "FYM + NPK", "amount": "5 tons + 80 kg/acre"},
                        {"time": "30 days", "type": "Urea", "amount": "40 kg/acre"}
                    ],
                    "irrigation": "5-7 irrigations",
                    "pest_control": [
                        {"time": "40 days", "issue": "Late blight", "treatment": "Fungicide spray"},
                        {"time": "60 days", "issue": "Aphids", "treatment": "Insecticide spray"}
                    ]
                }
            },
            "Tomato": {
                "North India": {
                    "planting": "July - August (Kharif), November (Rabi)",
                    "harvesting": "October - November, February - March",
                    "duration": "70-90 days",
                    "fertilizer_schedule": [
                        {"time": "At transplanting", "type": "FYM", "amount": "8 tons/acre"},
                        {"time": "15 days", "type": "NPK", "amount": "60 kg/acre"},
                        {"time": "35 days", "type": "Urea", "amount": "30 kg/acre"}
                    ],
                    "irrigation": "Weekly irrigation",
                    "pest_control": [
                        {"time": "25 days", "issue": "Fruit borer", "treatment": "Bt spray"},
                        {"time": "45 days", "issue": "Leaf curl", "treatment": "Remove affected plants"}
                    ]
                },
                "South India": {
                    "planting": "June - July, September - October",
                    "harvesting": "September - October, December - January",
                    "duration": "65-85 days",
                    "fertilizer_schedule": [
                        {"time": "At transplanting", "type": "Compost", "amount": "6 tons/acre"},
                        {"time": "20 days", "type": "NPK", "amount": "50 kg/acre"}
                    ],
                    "irrigation": "Drip irrigation preferred",
                    "pest_control": [
                        {"time": "30 days", "issue": "Whitefly", "treatment": "Neem spray"}
                    ]
                }
            }
        }
    
    def get_crop_schedule(self, crop: str, region: str) -> Optional[Dict]:
        """Get schedule for specific crop and region"""
        crop_data = self.crops.get(crop)
        if crop_data:
            return crop_data.get(region)
        return None
    
    def get_available_crops(self) -> List[str]:
        """Get list of available crops"""
        return list(self.crops.keys())
    
    def get_regions(self) -> List[str]:
        """Get list of regions"""
        return self.regions
    
    def get_crops_for_region(self, region: str) -> List[str]:
        """Get crops available for a region"""
        available = []
        for crop, regions in self.crops.items():
            if region in regions:
                available.append(crop)
        return available


# Global instance
_crop_calendar: CropCalendar = None


def get_crop_calendar() -> CropCalendar:
    """Get crop calendar instance"""
    global _crop_calendar
    
    if _crop_calendar is None:
        _crop_calendar = CropCalendar()
    
    return _crop_calendar


if __name__ == '__main__':
    # Test crop calendar
    calendar = get_crop_calendar()
    
    print("Crop Calendar Database")
    print("=" * 50)
    print(f"\nAvailable crops: {', '.join(calendar.get_available_crops())}")
    print(f"Regions: {', '.join(calendar.get_regions())}")
    
    print("\n\nWheat schedule for North India:")
    schedule = calendar.get_crop_schedule("Wheat", "North India")
    if schedule:
        print(f"Planting: {schedule['planting']}")
        print(f"Harvesting: {schedule['harvesting']}")
        print(f"Duration: {schedule['duration']}")
