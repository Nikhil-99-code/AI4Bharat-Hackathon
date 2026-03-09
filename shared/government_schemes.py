"""
Government Schemes Database for Indian Farmers
Information about agricultural subsidies and schemes
"""

from typing import List, Dict, Optional


class GovernmentSchemesDB:
    """Database of Indian government agricultural schemes"""
    
    def __init__(self):
        """Initialize schemes database"""
        self.schemes = self._load_schemes()
    
    def _load_schemes(self) -> List[Dict]:
        """Load government schemes data"""
        return [
            {
                'id': 'pmkisan',
                'name': 'PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)',
                'category': 'Income Support',
                'description': 'Direct income support of ₹6,000 per year to all farmer families',
                'eligibility': [
                    'All landholding farmer families',
                    'Small and marginal farmers',
                    'Must have cultivable land'
                ],
                'benefits': '₹6,000 per year in 3 installments of ₹2,000 each',
                'how_to_apply': 'Visit pmkisan.gov.in or nearest CSC/agriculture office',
                'documents': ['Aadhaar card', 'Land ownership documents', 'Bank account details'],
                'website': 'https://pmkisan.gov.in',
                'helpline': '155261 / 011-24300606'
            },
            {
                'id': 'pmfby',
                'name': 'PMFBY (Pradhan Mantri Fasal Bima Yojana)',
                'category': 'Crop Insurance',
                'description': 'Comprehensive crop insurance against natural calamities',
                'eligibility': [
                    'All farmers including sharecroppers',
                    'Covers all food & oilseed crops',
                    'Covers horticultural and commercial crops'
                ],
                'benefits': 'Coverage for crop loss due to natural calamities, pests, diseases',
                'premium': 'Kharif: 2%, Rabi: 1.5%, Horticultural: 5% of sum insured',
                'how_to_apply': 'Through banks, CSCs, or insurance companies',
                'documents': ['Land records', 'Aadhaar', 'Bank account', 'Sowing certificate'],
                'website': 'https://pmfby.gov.in',
                'helpline': '011-23382012'
            },
            {
                'id': 'kcc',
                'name': 'KCC (Kisan Credit Card)',
                'category': 'Credit/Loan',
                'description': 'Credit facility for farmers to meet agricultural expenses',
                'eligibility': [
                    'All farmers - individual/joint borrowers',
                    'Tenant farmers, oral lessees',
                    'SHGs or Joint Liability Groups'
                ],
                'benefits': 'Credit up to ₹3 lakh at 7% interest (4% with prompt repayment)',
                'how_to_apply': 'Apply at any bank branch',
                'documents': ['Land documents', 'Identity proof', 'Address proof'],
                'website': 'https://www.nabard.org/kcc.aspx',
                'helpline': 'Contact nearest bank branch'
            },
            {
                'id': 'pkvy',
                'name': 'PKVY (Paramparagat Krishi Vikas Yojana)',
                'category': 'Organic Farming',
                'description': 'Promotion of organic farming and certification',
                'eligibility': [
                    'Farmers practicing organic farming',
                    'Groups of 50 farmers forming clusters',
                    'Minimum 50 acres per cluster'
                ],
                'benefits': '₹50,000 per hectare over 3 years for organic inputs and certification',
                'how_to_apply': 'Through State Agriculture Department',
                'documents': ['Land records', 'Group formation certificate', 'Aadhaar'],
                'website': 'Contact State Agriculture Department',
                'helpline': 'State Agriculture Department'
            },
            {
                'id': 'pmksy',
                'name': 'PMKSY (Pradhan Mantri Krishi Sinchayee Yojana)',
                'category': 'Irrigation',
                'description': 'Improving water use efficiency through micro-irrigation',
                'eligibility': [
                    'All categories of farmers',
                    'Focus on small and marginal farmers',
                    'Self-help groups, cooperatives'
                ],
                'benefits': 'Subsidy for drip/sprinkler irrigation: 55% for small farmers, 45% for others',
                'how_to_apply': 'Through State Agriculture/Horticulture Department',
                'documents': ['Land ownership proof', 'Aadhaar', 'Bank account'],
                'website': 'Contact State Agriculture Department',
                'helpline': 'State Agriculture Department'
            },
            {
                'id': 'smam',
                'name': 'SMAM (Sub-Mission on Agricultural Mechanization)',
                'category': 'Equipment Subsidy',
                'description': 'Financial assistance for purchasing agricultural machinery',
                'eligibility': [
                    'Individual farmers',
                    'Groups of farmers, cooperatives',
                    'Custom Hiring Centers'
                ],
                'benefits': 'Subsidy: 40-50% for SC/ST/Small farmers, 40% for others (max ₹1.25 lakh)',
                'how_to_apply': 'Through State Agriculture Department portal',
                'documents': ['Land records', 'Caste certificate (if applicable)', 'Bank account'],
                'website': 'Contact State Agriculture Department',
                'helpline': 'State Agriculture Department'
            },
            {
                'id': 'nmoop',
                'name': 'NMOOP (National Mission on Oilseeds and Oil Palm)',
                'category': 'Crop Specific',
                'description': 'Support for oilseed cultivation and oil palm',
                'eligibility': [
                    'Farmers growing oilseeds',
                    'Oil palm cultivators',
                    'Farmer Producer Organizations'
                ],
                'benefits': 'Seeds, technology, market linkage support',
                'how_to_apply': 'Through State Agriculture Department',
                'documents': ['Land records', 'Aadhaar', 'Bank account'],
                'website': 'Contact State Agriculture Department',
                'helpline': 'State Agriculture Department'
            },
            {
                'id': 'soil_health',
                'name': 'Soil Health Card Scheme',
                'category': 'Soil Testing',
                'description': 'Free soil testing and health cards for farmers',
                'eligibility': [
                    'All farmers',
                    'Every 2 years per farm'
                ],
                'benefits': 'Free soil testing, nutrient recommendations, fertilizer advice',
                'how_to_apply': 'Visit nearest Soil Testing Laboratory or agriculture office',
                'documents': ['Land records', 'Aadhaar'],
                'website': 'https://soilhealth.dac.gov.in',
                'helpline': 'Contact nearest agriculture office'
            }
        ]
    
    def search_schemes(self, query: str = "", category: str = "") -> List[Dict]:
        """
        Search schemes by query or category
        
        Args:
            query: Search term (name, description)
            category: Filter by category
            
        Returns:
            List of matching schemes
        """
        results = self.schemes
        
        if category:
            results = [s for s in results if s['category'].lower() == category.lower()]
        
        if query:
            query_lower = query.lower()
            results = [
                s for s in results
                if query_lower in s['name'].lower() or
                   query_lower in s['description'].lower() or
                   query_lower in s['category'].lower()
            ]
        
        return results
    
    def get_scheme(self, scheme_id: str) -> Optional[Dict]:
        """Get scheme by ID"""
        for scheme in self.schemes:
            if scheme['id'] == scheme_id:
                return scheme
        return None
    
    def get_categories(self) -> List[str]:
        """Get all scheme categories"""
        return list(set(s['category'] for s in self.schemes))
    
    def get_all_schemes(self) -> List[Dict]:
        """Get all schemes"""
        return self.schemes


# Global instance
_schemes_db: GovernmentSchemesDB = None


def get_schemes_db() -> GovernmentSchemesDB:
    """Get schemes database instance"""
    global _schemes_db
    
    if _schemes_db is None:
        _schemes_db = GovernmentSchemesDB()
    
    return _schemes_db


if __name__ == '__main__':
    # Test schemes database
    db = get_schemes_db()
    
    print("Government Schemes Database")
    print("=" * 50)
    
    print(f"\nTotal schemes: {len(db.get_all_schemes())}")
    print(f"Categories: {', '.join(db.get_categories())}")
    
    print("\n\nSearching for 'insurance':")
    results = db.search_schemes("insurance")
    for scheme in results:
        print(f"  - {scheme['name']}")
    
    print("\n\nIncome Support schemes:")
    results = db.search_schemes(category="Income Support")
    for scheme in results:
        print(f"  - {scheme['name']}: {scheme['benefits']}")
