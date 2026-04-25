-- Venue database schema and seed data for AI Event Planner
-- Run via: python data/seed_db.py

CREATE TABLE IF NOT EXISTS venues (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT    NOT NULL,
    capacity_min        INTEGER NOT NULL,
    capacity_max        INTEGER NOT NULL,
    price_per_day_lkr   INTEGER NOT NULL,
    amenities_json      TEXT    NOT NULL,  -- JSON array of strings
    location            TEXT    NOT NULL,
    description         TEXT    NOT NULL,
    latitude            REAL    NOT NULL,
    longitude           REAL    NOT NULL
);

-- ─── Hotel Ballrooms ────────────────────────────────────────────────────────

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('Cinnamon Grand Ballroom', 100, 800, 450000,
 '["projector","screen","stage","av_equipment","catering","wifi","parking","ac","valet"]',
 'Colombo 3',
 'Grand ballroom inside the Cinnamon Grand Hotel, ideal for large corporate events, gala dinners, and product launches.',
 6.9157, 79.8490);

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('Hilton Colombo Grand Ballroom', 150, 1000, 500000,
 '["projector","screen","stage","av_equipment","catering","wifi","parking","ac","valet","breakout_rooms"]',
 'Colombo 1',
 'Flagship ballroom at Hilton Colombo, with professional AV setup and dedicated event staff. Suitable for conferences and large weddings.',
 6.9270, 79.8445);

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('Shangri-La Ballroom', 100, 700, 480000,
 '["projector","screen","stage","av_equipment","catering","wifi","parking","ac","valet","sea_view"]',
 'Colombo 1',
 'Elegant ballroom at Shangri-La Hotel with panoramic sea views, premium AV, and world-class catering.',
 6.9237, 79.8441);

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('Taj Samudra Grand Hall', 80, 600, 420000,
 '["projector","screen","stage","av_equipment","catering","wifi","parking","ac"]',
 'Colombo 3',
 'Spacious grand hall at the iconic Taj Samudra hotel, ideal for corporate events, seminars, and receptions.',
 6.9104, 79.8498);

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('Mount Lavinia Hotel Grand Ballroom', 80, 500, 350000,
 '["projector","screen","stage","av_equipment","catering","wifi","parking","ac","beach_access","outdoor"]',
 'Mount Lavinia',
 'Historic colonial ballroom steps from the beach. Perfect for weddings and evening receptions with outdoor overflow.',
 6.8301, 79.8649);

-- ─── Boutique & Mid-Range Event Spaces ───────────────────────────────────────

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('Lionel Wendt Art Centre', 30, 300, 180000,
 '["stage","ac","parking","projector","screen","sound_system"]',
 'Colombo 7',
 'Iconic arts venue with a main theatre, art gallery, and outdoor garden. Popular for cultural events, launches, and intimate gatherings.',
 6.9101, 79.8609);

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('British Council Auditorium', 20, 200, 120000,
 '["projector","screen","av_equipment","ac","wifi","stage"]',
 'Colombo 3',
 'Modern auditorium with excellent acoustics and AV facilities. Frequently used for tech talks, training, and panel discussions.',
 6.9100, 79.8510);

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('Galle Face Hotel Ballroom', 60, 400, 320000,
 '["projector","screen","stage","av_equipment","catering","wifi","parking","ac","sea_view"]',
 'Colombo 3',
 'Grand colonial ballroom at the Galle Face Hotel, with sea-facing terraces. Renowned for weddings and gala events.',
 6.9187, 79.8434);

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('Hotel Galadari Conference Hall', 50, 350, 200000,
 '["projector","screen","av_equipment","catering","wifi","parking","ac","breakout_rooms"]',
 'Colombo 1',
 'Purpose-built conference centre in the central business district with dedicated event management staff.',
 6.9246, 79.8434);

-- ─── Co-working & Tech Venues ─────────────────────────────────────────────

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('TRACE Expert City Hall', 30, 250, 150000,
 '["projector","screen","av_equipment","wifi","ac","catering","parking","stage"]',
 'Maligawatte, Colombo 10',
 'Modern tech-park event space within TRACE Expert City. The go-to venue for hackathons, tech meetups, and startup demo days.',
 6.9369, 79.8615);

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('Hatch Works Event Space', 20, 150, 90000,
 '["projector","screen","wifi","ac","catering","whiteboard"]',
 'Colombo 3',
 'Flexible co-working and event venue popular with the startup community. Can be configured for workshops, meetups, and small conferences.',
 6.9155, 79.8500);

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('Dialog Axiata HQ Auditorium', 50, 300, 160000,
 '["projector","screen","av_equipment","wifi","ac","parking","stage"]',
 'Colombo 3',
 'Corporate auditorium inside Dialog Axiata headquarters. Well-suited for tech summits, developer events, and large workshops.',
 6.9085, 79.8525);

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('Sri Lanka Institute of Information Technology (SLIIT) Auditorium', 50, 400, 80000,
 '["projector","screen","av_equipment","wifi","ac","parking","stage"]',
 'Malabe',
 'University auditorium available for community and corporate events. Affordable option for tech meetups and academic conferences.',
 6.9147, 79.9722);

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('IIT Auditorium', 30, 200, 85000,
 '["projector","screen","av_equipment","wifi","ac","parking"]',
 'Colombo 6',
 'Modern auditorium in Informatics Institute of Technology campus, ideal for workshops and corporate training.',
 6.8900, 79.8610);

-- ─── Garden & Outdoor Venues ──────────────────────────────────────────────

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('Viharamahadevi Park Amphitheatre', 100, 2000, 200000,
 '["stage","outdoor","parking","sound_system"]',
 'Colombo 7',
 'Open-air amphitheatre in the heart of Viharamahadevi Park. Ideal for large outdoor concerts, cultural festivals, and community events.',
 6.9104, 79.8587);

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('Hilton Colombo Garden Terrace', 40, 200, 250000,
 '["outdoor","catering","wifi","parking","ac","sea_view","stage"]',
 'Colombo 1',
 'Lush garden terrace at Hilton with sea views, ideal for outdoor cocktail receptions and small weddings.',
 6.9270, 79.8447);

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('Cinnamon Life Garden', 50, 300, 280000,
 '["outdoor","catering","wifi","parking","ac","stage","projector"]',
 'Colombo 2',
 'Contemporary outdoor event space at Cinnamon Life city resort, suitable for product launches and corporate evening events.',
 6.9202, 79.8487);

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('Royal Colombo Golf Club Event Lawn', 50, 400, 220000,
 '["outdoor","catering","parking","ac"]',
 'Colombo 7',
 'Expansive manicured lawn at the Royal Colombo Golf Club. Excellent for garden parties, charity galas, and outdoor receptions.',
 6.9066, 79.8648);

-- ─── Beachside Venues ─────────────────────────────────────────────────────

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('Mount Lavinia Beach Pavilion', 30, 200, 180000,
 '["outdoor","catering","beach_access","parking","sound_system"]',
 'Mount Lavinia',
 'Open-air pavilion directly on Mount Lavinia beach. A popular choice for sunset weddings and beach parties.',
 6.8290, 79.8666);

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('Lavinia Sunset Restaurant & Events', 20, 150, 130000,
 '["outdoor","catering","beach_access","parking","ac","sea_view"]',
 'Mount Lavinia',
 'Beachfront restaurant with an event deck. Intimate setting for private dinners, cocktail evenings, and small gatherings.',
 6.8295, 79.8663);

-- ─── Rooftop Venues ───────────────────────────────────────────────────────

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('Sky Lounge — Movenpick Hotel', 30, 150, 210000,
 '["outdoor","catering","wifi","bar","ac","sea_view","rooftop"]',
 'Colombo 3',
 'Rooftop bar and event space at Movenpick Hotel with panoramic city and sea views. Perfect for cocktail evenings and product launches.',
 6.9155, 79.8478);

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('The Rooftop — Sheraton Colombo', 40, 200, 260000,
 '["outdoor","catering","wifi","bar","ac","sea_view","rooftop","projector"]',
 'Colombo 3',
 'Upscale rooftop venue at Sheraton with full AV, catering, and 360° views. Ideal for networking events and evening receptions.',
 6.9124, 79.8479);

-- ─── Conference Centres ───────────────────────────────────────────────────

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('BMICH — Bandaranaike Memorial International Conference Hall', 200, 1500, 380000,
 '["projector","screen","stage","av_equipment","catering","wifi","parking","ac","breakout_rooms","simultaneous_translation"]',
 'Colombo 7',
 'Sri Lanka''s premier international conference centre. Used for government summits, large-scale exhibitions, and international conventions.',
 6.9121, 79.8643);

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('SLECC — Sri Lanka Exhibition & Convention Centre', 100, 2000, 400000,
 '["projector","screen","stage","av_equipment","catering","wifi","parking","ac","breakout_rooms","exhibition_hall"]',
 'Colombo 1',
 'State-of-the-art convention and exhibition centre adjacent to the Beira Lake. Hosts international trade shows and large conferences.',
 6.9264, 79.8390);

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('Waters Edge Conference Centre', 50, 500, 290000,
 '["projector","screen","stage","av_equipment","catering","wifi","parking","ac","outdoor","lake_view"]',
 'Battaramulla',
 'Scenic conference and banquet complex beside a lake. Popular for corporate retreats, training programmes, and wedding receptions.',
 6.8997, 79.9148);

-- ─── Community & Cultural Venues ──────────────────────────────────────────

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('Stein Studios Event Hall', 20, 120, 75000,
 '["projector","screen","wifi","ac","catering","stage"]',
 'Colombo 5',
 'Boutique creative studio space adaptable for workshops, product demos, networking events, and photo shoots.',
 6.8930, 79.8612);

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('Nelum Pokuna Amphitheatre', 150, 1200, 300000,
 '["stage","outdoor","parking","ac","sound_system","projector","screen"]',
 'Colombo 7',
 'Iconic open-air amphitheatre designed for large concerts and cultural performances. Also available for corporate spectaculars.',
 6.9089, 79.8656);

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('Ramada Colombo Conference Room', 20, 100, 95000,
 '["projector","screen","av_equipment","wifi","ac","catering","parking"]',
 'Colombo 2',
 'Compact conference rooms at Ramada Colombo suitable for board meetings, training sessions, and small workshops.',
 6.9195, 79.8498);

INSERT INTO venues (name, capacity_min, capacity_max, price_per_day_lkr, amenities_json, location, description, latitude, longitude) VALUES
('Cinnamon Red Event Space', 30, 200, 140000,
 '["projector","screen","wifi","ac","catering","parking","rooftop"]',
 'Colombo 10',
 'Contemporary event space at Cinnamon Red hotel, versatile for corporate dinners, product launches, and networking evenings.',
 6.9280, 79.8610);
