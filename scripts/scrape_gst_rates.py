"""
GST Rate Generator
Generates GST rates based on official CBIC data and GST Council notifications
Based on September 2025 GST reforms (56th GST Council Meeting)
"""

import json
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import re

# Paths
BASE_DIR = Path(__file__).parent.parent
DB_DIR = BASE_DIR / "db"
GST_RATES_DIR = DB_DIR / "gst_rates"
DOWNLOADS_DIR = BASE_DIR / "downloads"

# Create directories
DOWNLOADS_DIR.mkdir(exist_ok=True)
GST_RATES_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# OFFICIAL DATA SOURCES
# =============================================================================

# Primary source: ClearTax (well-structured, frequently updated)
CLEARTAX_GOODS_URL = "https://cleartax.in/s/gst-rates-hsn-codes"
CLEARTAX_SERVICES_URL = "https://cleartax.in/s/gst-rate-on-services-sac-codes"

# Government sources (PDFs - harder to parse)
CBIC_GST_URL = "https://cbic-gst.gov.in/gst-goods-services-rates.html"
GST_PORTAL_URL = "https://www.gst.gov.in/"


# =============================================================================
# GST RATE DATA (2025 Reforms - September 22, 2025)
# =============================================================================

# Based on GST Council 56th Meeting (September 2025)
# Simplified to 3-tier: 5%, 18%, 40% (with some exemptions at 0%)

GST_GOODS_RATES_2025 = [
    # EXEMPT (0%)
    {"hsn_code": "0401", "item_name": "Fresh Milk", "category": "dairy", "gst_rate": 0, "cess_rate": 0, "notes": "Exempt - Essential"},
    {"hsn_code": "0403", "item_name": "Curd, Lassi, Buttermilk", "category": "dairy", "gst_rate": 0, "cess_rate": 0, "notes": "Exempt - Essential"},
    {"hsn_code": "0406", "item_name": "Paneer, Cheese", "category": "dairy", "gst_rate": 0, "cess_rate": 0, "notes": "Exempt - Essential"},
    {"hsn_code": "0701-0714", "item_name": "Fresh Vegetables", "category": "food", "gst_rate": 0, "cess_rate": 0, "notes": "Exempt - Unprocessed"},
    {"hsn_code": "0801-0814", "item_name": "Fresh Fruits", "category": "food", "gst_rate": 0, "cess_rate": 0, "notes": "Exempt - Unprocessed"},
    {"hsn_code": "1001", "item_name": "Wheat", "category": "cereals", "gst_rate": 0, "cess_rate": 0, "notes": "Exempt - Essential"},
    {"hsn_code": "1006", "item_name": "Rice", "category": "cereals", "gst_rate": 0, "cess_rate": 0, "notes": "Exempt - Essential"},
    {"hsn_code": "0713", "item_name": "Pulses (Dried)", "category": "food", "gst_rate": 0, "cess_rate": 0, "notes": "Exempt - Essential"},
    {"hsn_code": "2501", "item_name": "Salt", "category": "food", "gst_rate": 0, "cess_rate": 0, "notes": "Exempt - Essential"},
    {"hsn_code": "0207", "item_name": "Fresh/Chilled Meat", "category": "meat", "gst_rate": 0, "cess_rate": 0, "notes": "Exempt - Unprocessed"},
    {"hsn_code": "0302-0307", "item_name": "Fresh Fish", "category": "seafood", "gst_rate": 0, "cess_rate": 0, "notes": "Exempt - Unprocessed"},
    {"hsn_code": "0407", "item_name": "Eggs", "category": "food", "gst_rate": 0, "cess_rate": 0, "notes": "Exempt - Essential"},
    {"hsn_code": "1101", "item_name": "Wheat Flour (Atta)", "category": "cereals", "gst_rate": 0, "cess_rate": 0, "notes": "Exempt - Unbranded"},
    {"hsn_code": "1102", "item_name": "Cereal Flours", "category": "cereals", "gst_rate": 0, "cess_rate": 0, "notes": "Exempt - Unbranded"},
    {"hsn_code": "4901", "item_name": "Printed Books, Newspapers", "category": "education", "gst_rate": 0, "cess_rate": 0, "notes": "Exempt"},
    {"hsn_code": "3004", "item_name": "Life-saving Drugs (Specified)", "category": "pharma", "gst_rate": 0, "cess_rate": 0, "notes": "Exempt - 33 specified drugs"},
    
    # 5% (Merit Rate)
    {"hsn_code": "0901", "item_name": "Coffee", "category": "beverages", "gst_rate": 5, "cess_rate": 0, "notes": "Merit Rate"},
    {"hsn_code": "0902", "item_name": "Tea", "category": "beverages", "gst_rate": 5, "cess_rate": 0, "notes": "Merit Rate"},
    {"hsn_code": "1701", "item_name": "Sugar", "category": "food", "gst_rate": 5, "cess_rate": 0, "notes": "Merit Rate"},
    {"hsn_code": "1507-1518", "item_name": "Edible Oils", "category": "food", "gst_rate": 5, "cess_rate": 0, "notes": "Merit Rate"},
    {"hsn_code": "1905", "item_name": "Bread, Biscuits", "category": "bakery", "gst_rate": 5, "cess_rate": 0, "notes": "Merit Rate"},
    {"hsn_code": "2106", "item_name": "Food Preparations NES", "category": "food", "gst_rate": 5, "cess_rate": 0, "notes": "Merit Rate - Packaged"},
    {"hsn_code": "3306", "item_name": "Toothpaste", "category": "fmcg", "gst_rate": 5, "cess_rate": 0, "notes": "Merit Rate - 2025 Reform"},
    {"hsn_code": "3305", "item_name": "Hair Oil, Shampoo", "category": "fmcg", "gst_rate": 5, "cess_rate": 0, "notes": "Merit Rate - 2025 Reform"},
    {"hsn_code": "3401", "item_name": "Soap", "category": "fmcg", "gst_rate": 5, "cess_rate": 0, "notes": "Merit Rate - 2025 Reform"},
    {"hsn_code": "3402", "item_name": "Detergent", "category": "fmcg", "gst_rate": 5, "cess_rate": 0, "notes": "Merit Rate - 2025 Reform"},
    {"hsn_code": "4802", "item_name": "Paper, Notebooks", "category": "stationery", "gst_rate": 5, "cess_rate": 0, "notes": "Merit Rate"},
    {"hsn_code": "6101-6117", "item_name": "Garments (Below ₹1000)", "category": "apparel", "gst_rate": 5, "cess_rate": 0, "notes": "Merit Rate - Value based"},
    {"hsn_code": "6401-6405", "item_name": "Footwear (Below ₹1000)", "category": "footwear", "gst_rate": 5, "cess_rate": 0, "notes": "Merit Rate - Value based"},
    {"hsn_code": "8432-8436", "item_name": "Agricultural Machinery", "category": "machinery", "gst_rate": 5, "cess_rate": 0, "notes": "Merit Rate"},
    {"hsn_code": "8701", "item_name": "Tractors", "category": "agriculture", "gst_rate": 5, "cess_rate": 0, "notes": "Merit Rate"},
    {"hsn_code": "3102-3105", "item_name": "Fertilizers", "category": "agriculture", "gst_rate": 5, "cess_rate": 0, "notes": "Merit Rate"},
    {"hsn_code": "3808", "item_name": "Pesticides, Insecticides", "category": "agriculture", "gst_rate": 5, "cess_rate": 0, "notes": "Merit Rate"},
    {"hsn_code": "3003", "item_name": "Medicines (Bulk)", "category": "pharma", "gst_rate": 5, "cess_rate": 0, "notes": "Merit Rate"},
    {"hsn_code": "3004", "item_name": "Medicines (Formulation)", "category": "pharma", "gst_rate": 5, "cess_rate": 0, "notes": "Merit Rate - General"},
    {"hsn_code": "9018-9022", "item_name": "Medical Equipment", "category": "medical", "gst_rate": 5, "cess_rate": 0, "notes": "Merit Rate"},
    {"hsn_code": "8712", "item_name": "Bicycles", "category": "transport", "gst_rate": 5, "cess_rate": 0, "notes": "Merit Rate"},
    {"hsn_code": "9401", "item_name": "Furniture (Cane/Bamboo)", "category": "furniture", "gst_rate": 5, "cess_rate": 0, "notes": "Merit Rate"},
    
    # 18% (Standard Rate)
    {"hsn_code": "8415", "item_name": "Air Conditioner", "category": "appliances", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "8418", "item_name": "Refrigerator", "category": "appliances", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "8450", "item_name": "Washing Machine", "category": "appliances", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "8451", "item_name": "Dryer, Ironing Machine", "category": "appliances", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "8471", "item_name": "Computers, Laptops", "category": "electronics", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "8517", "item_name": "Mobile Phones, Smartphones", "category": "electronics", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "8528", "item_name": "Television, Monitors", "category": "electronics", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "8519", "item_name": "Audio Equipment", "category": "electronics", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "8443", "item_name": "Printers, Scanners", "category": "electronics", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "8473", "item_name": "Computer Parts", "category": "electronics", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "8504", "item_name": "Transformers, Inverters", "category": "electrical", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "8506", "item_name": "Batteries", "category": "electrical", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "8507", "item_name": "Li-ion Batteries", "category": "electrical", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "8539", "item_name": "LED Lights, Bulbs", "category": "electrical", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "2523", "item_name": "Cement", "category": "construction", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate - 2025 Reform (was 28%)"},
    {"hsn_code": "7213-7217", "item_name": "Iron/Steel Products", "category": "construction", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "7601-7616", "item_name": "Aluminium Products", "category": "metals", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "3208-3210", "item_name": "Paints, Varnishes", "category": "construction", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "6907-6908", "item_name": "Ceramic Tiles", "category": "construction", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "6802-6810", "item_name": "Marble, Granite, Stone", "category": "construction", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "3923-3926", "item_name": "Plastic Products", "category": "plastics", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "9401-9403", "item_name": "Furniture (Metal/Wood)", "category": "furniture", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "9404", "item_name": "Mattresses", "category": "furniture", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "6101-6117", "item_name": "Garments (₹1000 and above)", "category": "apparel", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate - Value based"},
    {"hsn_code": "6401-6405", "item_name": "Footwear (₹1000 and above)", "category": "footwear", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate - Value based"},
    {"hsn_code": "9101-9114", "item_name": "Watches, Clocks", "category": "accessories", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "7113-7117", "item_name": "Imitation Jewellery", "category": "accessories", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "8703", "item_name": "Small Cars (Petrol <1200cc, Diesel <1500cc)", "category": "automobiles", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate - No Cess"},
    {"hsn_code": "8711", "item_name": "Motorcycles (≤350cc)", "category": "automobiles", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "4011-4013", "item_name": "Tyres, Tubes", "category": "automobiles", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "2710", "item_name": "Lubricating Oils", "category": "petroleum", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "3301-3307", "item_name": "Cosmetics, Perfumes", "category": "cosmetics", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "4202", "item_name": "Bags, Wallets, Luggage", "category": "accessories", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "9503-9508", "item_name": "Toys, Games", "category": "toys", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "9504", "item_name": "Video Games", "category": "entertainment", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "8414", "item_name": "Fans, Blowers", "category": "appliances", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    {"hsn_code": "8516", "item_name": "Electric Heaters, Geysers", "category": "appliances", "gst_rate": 18, "cess_rate": 0, "notes": "Standard Rate"},
    
    # 28% + Cess (Luxury/Sin)
    {"hsn_code": "2402", "item_name": "Cigarettes", "category": "tobacco", "gst_rate": 28, "cess_rate": "variable", "notes": "Sin Tax + Cess"},
    {"hsn_code": "2403", "item_name": "Tobacco Products", "category": "tobacco", "gst_rate": 28, "cess_rate": "variable", "notes": "Sin Tax + Cess"},
    {"hsn_code": "2106", "item_name": "Pan Masala (with tobacco)", "category": "tobacco", "gst_rate": 28, "cess_rate": "variable", "notes": "Sin Tax + Cess"},
    {"hsn_code": "2202", "item_name": "Aerated Drinks", "category": "beverages", "gst_rate": 28, "cess_rate": 12, "notes": "Sin Tax + 12% Cess"},
    {"hsn_code": "2202", "item_name": "Energy Drinks", "category": "beverages", "gst_rate": 28, "cess_rate": 12, "notes": "Sin Tax + 12% Cess"},
    {"hsn_code": "8703", "item_name": "Large Cars (Petrol >1200cc)", "category": "automobiles", "gst_rate": 28, "cess_rate": 15, "notes": "Luxury + 15% Cess"},
    {"hsn_code": "8703", "item_name": "Large Cars (Diesel >1500cc)", "category": "automobiles", "gst_rate": 28, "cess_rate": 15, "notes": "Luxury + 15% Cess"},
    {"hsn_code": "8703", "item_name": "SUVs (Length >4m, Engine >1500cc)", "category": "automobiles", "gst_rate": 28, "cess_rate": 22, "notes": "Luxury + 22% Cess"},
    {"hsn_code": "8711", "item_name": "Motorcycles (>350cc)", "category": "automobiles", "gst_rate": 28, "cess_rate": 3, "notes": "Luxury + 3% Cess"},
    {"hsn_code": "8903", "item_name": "Yachts, Boats", "category": "luxury", "gst_rate": 28, "cess_rate": 0, "notes": "Luxury"},
    {"hsn_code": "8802", "item_name": "Private Aircraft", "category": "luxury", "gst_rate": 28, "cess_rate": 0, "notes": "Luxury"},
    {"hsn_code": "9302-9305", "item_name": "Firearms", "category": "luxury", "gst_rate": 28, "cess_rate": 0, "notes": "Luxury"},
    {"hsn_code": "7101-7104", "item_name": "Precious Stones (Unset)", "category": "luxury", "gst_rate": 0.25, "cess_rate": 0, "notes": "Special Rate"},
    {"hsn_code": "7106-7112", "item_name": "Gold, Silver, Platinum", "category": "precious_metals", "gst_rate": 3, "cess_rate": 0, "notes": "Special Rate"},
]


GST_SERVICES_RATES_2025 = [
    # EXEMPT (0%)
    {"sac_code": "9992", "service_name": "Education Services", "category": "education", "gst_rate": 0, "condition": "Recognized institutions", "notes": "Exempt"},
    {"sac_code": "9993", "service_name": "Healthcare Services", "category": "healthcare", "gst_rate": 0, "condition": "Clinical establishments", "notes": "Exempt"},
    {"sac_code": "997131", "service_name": "Life Insurance", "category": "insurance", "gst_rate": 0, "condition": "Pure term life", "notes": "Exempt - 2025 Reform"},
    {"sac_code": "997133", "service_name": "Health Insurance", "category": "insurance", "gst_rate": 0, "condition": "", "notes": "Exempt - 2025 Reform"},
    {"sac_code": "9965", "service_name": "Public Transport (Metro/Bus/Train)", "category": "transport", "gst_rate": 0, "condition": "Public transport", "notes": "Exempt"},
    {"sac_code": "9972", "service_name": "Residential Rent", "category": "real_estate", "gst_rate": 0, "condition": "Residential property", "notes": "Exempt"},
    {"sac_code": "9954", "service_name": "Affordable Housing", "category": "real_estate", "gst_rate": 0, "condition": "Under PMAY", "notes": "Exempt"},
    {"sac_code": "9991", "service_name": "Government Services", "category": "government", "gst_rate": 0, "condition": "Sovereign functions", "notes": "Exempt"},
    
    # 5% (Merit Rate)
    {"sac_code": "9963", "service_name": "Hotel Stay (Below ₹7500)", "category": "hospitality", "gst_rate": 5, "condition": "Tariff < ₹7500/day", "notes": "Merit Rate"},
    {"sac_code": "9963", "service_name": "Restaurant (Non-AC)", "category": "hospitality", "gst_rate": 5, "condition": "Without ITC", "notes": "Merit Rate"},
    {"sac_code": "9996", "service_name": "Gym/Fitness Services", "category": "wellness", "gst_rate": 5, "condition": "", "notes": "Merit Rate - 2025 Reform"},
    {"sac_code": "9997", "service_name": "Salon/Beauty Services", "category": "wellness", "gst_rate": 5, "condition": "", "notes": "Merit Rate - 2025 Reform"},
    {"sac_code": "9988", "service_name": "Job Work (Manufacturing)", "category": "manufacturing", "gst_rate": 5, "condition": "For registered person", "notes": "Merit Rate"},
    {"sac_code": "9965", "service_name": "Goods Transport (GTA)", "category": "transport", "gst_rate": 5, "condition": "Without ITC", "notes": "Merit Rate - Option A"},
    {"sac_code": "9966", "service_name": "Passenger Transport (Non-AC)", "category": "transport", "gst_rate": 5, "condition": "Non-AC bus/cab", "notes": "Merit Rate"},
    {"sac_code": "9967", "service_name": "Courier/Postal Services", "category": "logistics", "gst_rate": 5, "condition": "", "notes": "Merit Rate - 2025 Reform"},
    {"sac_code": "9985", "service_name": "Housekeeping Services", "category": "services", "gst_rate": 5, "condition": "", "notes": "Merit Rate"},
    {"sac_code": "9986", "service_name": "Event Management (Small)", "category": "entertainment", "gst_rate": 5, "condition": "Value < ₹2.5L", "notes": "Merit Rate"},
    
    # 12% (Intermediate Rate)
    {"sac_code": "9965", "service_name": "Goods Transport (GTA with ITC)", "category": "transport", "gst_rate": 12, "condition": "With ITC", "notes": "Intermediate Rate"},
    {"sac_code": "9964", "service_name": "Air Travel (Economy)", "category": "transport", "gst_rate": 5, "condition": "Economy class", "notes": "Merit Rate"},
    {"sac_code": "9967", "service_name": "Tour Operator Services", "category": "travel", "gst_rate": 5, "condition": "Without ITC", "notes": "Merit Rate"},
    
    # 18% (Standard Rate)
    {"sac_code": "9971", "service_name": "Banking Services", "category": "financial", "gst_rate": 18, "condition": "", "notes": "Standard Rate"},
    {"sac_code": "9971", "service_name": "Insurance (General)", "category": "insurance", "gst_rate": 18, "condition": "Except Health/Life", "notes": "Standard Rate"},
    {"sac_code": "9971", "service_name": "Stock Broking", "category": "financial", "gst_rate": 18, "condition": "", "notes": "Standard Rate"},
    {"sac_code": "9972", "service_name": "Commercial Rent", "category": "real_estate", "gst_rate": 18, "condition": "Commercial property", "notes": "Standard Rate"},
    {"sac_code": "9954", "service_name": "Construction Services", "category": "construction", "gst_rate": 18, "condition": "Commercial", "notes": "Standard Rate"},
    {"sac_code": "9982", "service_name": "Legal Services", "category": "professional", "gst_rate": 18, "condition": "", "notes": "Standard Rate"},
    {"sac_code": "9982", "service_name": "Accounting/Audit Services", "category": "professional", "gst_rate": 18, "condition": "", "notes": "Standard Rate"},
    {"sac_code": "9983", "service_name": "IT/Software Services", "category": "technology", "gst_rate": 18, "condition": "", "notes": "Standard Rate"},
    {"sac_code": "9983", "service_name": "Consulting Services", "category": "professional", "gst_rate": 18, "condition": "", "notes": "Standard Rate"},
    {"sac_code": "9983", "service_name": "Management Services", "category": "professional", "gst_rate": 18, "condition": "", "notes": "Standard Rate"},
    {"sac_code": "9983", "service_name": "Advertising/Marketing", "category": "media", "gst_rate": 18, "condition": "", "notes": "Standard Rate"},
    {"sac_code": "9984", "service_name": "Telecom Services", "category": "telecom", "gst_rate": 18, "condition": "", "notes": "Standard Rate"},
    {"sac_code": "9973", "service_name": "IP/Licensing Services", "category": "technology", "gst_rate": 18, "condition": "", "notes": "Standard Rate"},
    {"sac_code": "9981", "service_name": "R&D Services", "category": "technology", "gst_rate": 18, "condition": "", "notes": "Standard Rate"},
    {"sac_code": "9963", "service_name": "Hotel Stay (₹7500 and above)", "category": "hospitality", "gst_rate": 18, "condition": "Tariff >= ₹7500", "notes": "Standard Rate"},
    {"sac_code": "9963", "service_name": "Restaurant (AC/5-star)", "category": "hospitality", "gst_rate": 18, "condition": "With ITC", "notes": "Standard Rate"},
    {"sac_code": "9964", "service_name": "Air Travel (Business Class)", "category": "transport", "gst_rate": 12, "condition": "Business/First", "notes": "Intermediate Rate"},
    {"sac_code": "9966", "service_name": "Passenger Transport (AC)", "category": "transport", "gst_rate": 18, "condition": "AC cab/bus", "notes": "Standard Rate"},
    {"sac_code": "9968", "service_name": "Warehousing Services", "category": "logistics", "gst_rate": 18, "condition": "", "notes": "Standard Rate"},
    {"sac_code": "9995", "service_name": "Membership Services", "category": "services", "gst_rate": 18, "condition": "", "notes": "Standard Rate"},
    {"sac_code": "9996", "service_name": "Recreational Services", "category": "entertainment", "gst_rate": 18, "condition": "", "notes": "Standard Rate"},
    {"sac_code": "9986", "service_name": "Event Management", "category": "entertainment", "gst_rate": 18, "condition": "", "notes": "Standard Rate"},
    {"sac_code": "9987", "service_name": "Maintenance/Repair Services", "category": "services", "gst_rate": 18, "condition": "", "notes": "Standard Rate"},
    {"sac_code": "9989", "service_name": "Manufacturing Services", "category": "manufacturing", "gst_rate": 18, "condition": "On job work basis", "notes": "Standard Rate"},
    {"sac_code": "9997", "service_name": "Other Personal Services", "category": "services", "gst_rate": 18, "condition": "", "notes": "Standard Rate"},
    
    # 28% (Luxury/Entertainment)
    {"sac_code": "9996", "service_name": "Casino, Gambling", "category": "entertainment", "gst_rate": 28, "condition": "", "notes": "Luxury - 2023 Amendment"},
    {"sac_code": "9996", "service_name": "Horse Racing", "category": "entertainment", "gst_rate": 28, "condition": "", "notes": "Luxury"},
    {"sac_code": "9996", "service_name": "Online Gaming (Money)", "category": "entertainment", "gst_rate": 28, "condition": "Real money gaming", "notes": "Luxury - 2023 Amendment"},
    {"sac_code": "9996", "service_name": "Lottery Services", "category": "entertainment", "gst_rate": 28, "condition": "", "notes": "Luxury"},
]


def save_goods_rates_csv():
    """Save goods rates to CSV."""
    output_file = GST_RATES_DIR / "goods_rates_2025.csv"
    
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["hsn_code", "item_name", "category", "gst_rate", "cess_rate", "effective_from", "notes"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for item in GST_GOODS_RATES_2025:
            row = {
                "hsn_code": item["hsn_code"],
                "item_name": item["item_name"],
                "category": item["category"],
                "gst_rate": item["gst_rate"],
                "cess_rate": item.get("cess_rate", 0),
                "effective_from": "2025-09-22",
                "notes": item.get("notes", "")
            }
            writer.writerow(row)
    
    print(f"✅ Saved {len(GST_GOODS_RATES_2025)} goods rates to {output_file}")
    return output_file


def save_services_rates_csv():
    """Save services rates to CSV."""
    output_file = GST_RATES_DIR / "services_rates_2025.csv"
    
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["sac_code", "service_name", "category", "gst_rate", "effective_from", "condition", "notes"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for item in GST_SERVICES_RATES_2025:
            row = {
                "sac_code": item["sac_code"],
                "service_name": item["service_name"],
                "category": item["category"],
                "gst_rate": item["gst_rate"],
                "effective_from": "2025-09-22",
                "condition": item.get("condition", ""),
                "notes": item.get("notes", "")
            }
            writer.writerow(row)
    
    print(f"✅ Saved {len(GST_SERVICES_RATES_2025)} services rates to {output_file}")
    return output_file


def save_master_json():
    """Save complete GST data to JSON."""
    output_file = DB_DIR / "gst_rates_2025.json"
    
    data = {
        "_metadata": {
            "version": "2025.2",
            "effective_from": "2025-09-22",
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "source": "GST Council 56th Meeting (Sept 2025)",
            "notes": "Simplified 3-tier structure: 5%, 18%, 28%+Cess"
        },
        "slabs": {
            "exempt": {"rate": 0, "description": "Essential goods and services"},
            "merit": {"rate": 5, "description": "Mass consumption goods"},
            "standard": {"rate": 18, "description": "Standard rate for most goods/services"},
            "luxury": {"rate": 28, "description": "Luxury and sin goods + Cess"}
        },
        "goods": GST_GOODS_RATES_2025,
        "services": GST_SERVICES_RATES_2025,
        "msme_classification": {
            "effective_from": "2020-07-01",
            "categories": {
                "micro": {"investment_limit": 10000000, "turnover_limit": 50000000},
                "small": {"investment_limit": 100000000, "turnover_limit": 500000000},
                "medium": {"investment_limit": 500000000, "turnover_limit": 2500000000}
            }
        },
        "compliance_rules": {
            "section_43b_h": {
                "payment_limit_days": 45,
                "applies_to": ["micro", "small"],
                "effective_from": "2024-04-01"
            }
        }
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved master JSON to {output_file}")
    return output_file


def main():
    """Run the GST rate data generation."""
    print("=" * 60)
    print("📊 GST Rate Data Generator")
    print("=" * 60)
    print(f"\nBased on: GST Council 56th Meeting (September 2025)")
    print(f"Key Change: Simplified to 5%, 18%, 28% (with exemptions)\n")
    
    # Save files
    save_goods_rates_csv()
    save_services_rates_csv()
    save_master_json()
    
    print("\n" + "=" * 60)
    print("✅ All GST rate files generated successfully!")
    print("=" * 60)
    
    # Summary
    print("\n📁 Files created in db/:")
    print(f"   - gst_rates/goods_rates_2025.csv ({len(GST_GOODS_RATES_2025)} items)")
    print(f"   - gst_rates/services_rates_2025.csv ({len(GST_SERVICES_RATES_2025)} items)")
    print(f"   - gst_rates_2025.json (Master file)")
    
    print("\n⚠️  Note: This data is based on September 2025 GST reforms.")
    print("   Always verify against official CBIC notifications for compliance.")


if __name__ == "__main__":
    main()

