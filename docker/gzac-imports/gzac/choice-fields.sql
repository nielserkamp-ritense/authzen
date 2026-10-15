-- Choice fields for the eerstelijns-klachten demo (F2/S2).
--
-- Runs after init-db.sql on a fresh gzac-database volume; changes need `./run.sh --reset`.
-- `name` is the key used by forms, DMN, gateways and policies; `value` is the label shown in the UI.
-- Cascades use the `.name` of a selected value as the next choice-field key:
--   DIENSTEN -> {DIENST}_SECTOR -> {DIENST}_SECTOR_{X} (afdelingen)
--   DIENSTVERLENINGSPRINCIPES / BEHOORLIJKHEIDSNORMEN -> KERNWAARDE_* (vereisten)
-- Kernwaarden and vereisten follow the Nationale ombudsman behoorlijkheidswijzer (2026).

SET search_path = public;

INSERT INTO choice_fields (key_name, title, created_by) VALUES
    ('DIENSTEN', 'Diensten', 'system'),
    ('AUTORISATIEGROEPEN_OCW', 'Autorisatiegroepen OCW', 'system'),
    ('AUTORISATIEGROEPEN_SZW', 'Autorisatiegroepen SZW', 'system'),
    ('AUTORISATIEGROEPEN_DPZ', 'Autorisatiegroepen DPZ', 'system'),
    ('AUTORISATIEGROEPEN_DSB', 'Autorisatiegroepen DSB', 'system'),
    ('AUTORISATIEGROEPEN_DSO', 'Autorisatiegroepen DSO', 'system'),
    ('AUTORISATIEGROEPEN_DBV', 'Autorisatiegroepen DBV', 'system'),
    ('AUTORISATIEGROEPEN_BSD', 'Autorisatiegroepen BSD', 'system'),
    ('AUTORISATIEGROEPEN_GGD', 'Autorisatiegroepen GGD', 'system'),
    ('AUTORISATIEGROEPEN_VTH', 'Autorisatiegroepen VTH', 'system'),
    ('OCW_SECTOR', 'Sectoren OCW', 'system'),
    ('OCW_SECTOR_ONDERWIJS', 'Afdelingen OCW Onderwijs', 'system'),
    ('OCW_SECTOR_JEUGD', 'Afdelingen OCW Jeugd', 'system'),
    ('OCW_SECTOR_WELZIJN', 'Afdelingen OCW Welzijn', 'system'),
    ('OCW_SECTOR_CULTUUR', 'Afdelingen OCW Cultuur', 'system'),
    ('OCW_SECTOR_SPORT', 'Afdelingen OCW Sport', 'system'),
    ('SZW_SECTOR', 'Sectoren SZW', 'system'),
    ('SZW_SECTOR_WERK_EN_INKOMEN', 'Afdelingen SZW Werk en Inkomen', 'system'),
    ('SZW_SECTOR_ZORG', 'Afdelingen SZW Zorg', 'system'),
    ('SZW_SECTOR_SCHULDEN', 'Afdelingen SZW Schulden', 'system'),
    ('SZW_SECTOR_PARTICIPATIE', 'Afdelingen SZW Participatie', 'system'),
    ('DPZ_SECTOR', 'Sectoren DPZ', 'system'),
    ('DPZ_SECTOR_BURGERZAKEN', 'Afdelingen DPZ Burgerzaken', 'system'),
    ('DPZ_SECTOR_BELASTINGEN', 'Afdelingen DPZ Belastingen', 'system'),
    ('DPZ_SECTOR_PARKEREN', 'Afdelingen DPZ Parkeren', 'system'),
    ('DPZ_SECTOR_KLANTCONTACT', 'Afdelingen DPZ Klantcontact', 'system'),
    ('DSB_SECTOR', 'Sectoren DSB', 'system'),
    ('DSB_SECTOR_AFVAL', 'Afdelingen DSB Afval', 'system'),
    ('DSB_SECTOR_OPENBARE_RUIMTE', 'Afdelingen DSB Openbare ruimte', 'system'),
    ('DSB_SECTOR_GROEN', 'Afdelingen DSB Groen', 'system'),
    ('DSB_SECTOR_HANDHAVING', 'Afdelingen DSB Handhaving', 'system'),
    ('DSO_SECTOR', 'Sectoren DSO', 'system'),
    ('DSO_SECTOR_RUIMTELIJKE_ORDENING', 'Afdelingen DSO Ruimtelijke ordening', 'system'),
    ('DSO_SECTOR_VERGUNNINGEN', 'Afdelingen DSO Vergunningen', 'system'),
    ('DSO_SECTOR_MOBILITEIT', 'Afdelingen DSO Mobiliteit', 'system'),
    ('DSO_SECTOR_WONEN', 'Afdelingen DSO Wonen', 'system'),
    ('DBV_SECTOR', 'Sectoren DBV', 'system'),
    ('DBV_SECTOR_ICT', 'Afdelingen DBV ICT', 'system'),
    ('DBV_SECTOR_FINANCIEN', 'Afdelingen DBV Financiën', 'system'),
    ('DBV_SECTOR_INKOOP', 'Afdelingen DBV Inkoop', 'system'),
    ('DBV_SECTOR_HR', 'Afdelingen DBV HR', 'system'),
    ('BSD_SECTOR', 'Sectoren BSD', 'system'),
    ('BSD_SECTOR_BESTUURSZAKEN', 'Afdelingen BSD Bestuurszaken', 'system'),
    ('BSD_SECTOR_COMMUNICATIE', 'Afdelingen BSD Communicatie', 'system'),
    ('BSD_SECTOR_JURIDISCHE_ZAKEN', 'Afdelingen BSD Juridische zaken', 'system'),
    ('GGD_SECTOR', 'Sectoren GGD', 'system'),
    ('GGD_SECTOR_INFECTIEZIEKTEN', 'Afdelingen GGD Infectieziekten', 'system'),
    ('GGD_SECTOR_MILIEU_EN_GEZONDHEID', 'Afdelingen GGD Milieu en gezondheid', 'system'),
    ('GGD_SECTOR_FORENSISCHE_GENEESKUNDE', 'Afdelingen GGD Forensische geneeskunde', 'system'),
    ('GGD_SECTOR_AMBULANCEZORG', 'Afdelingen GGD Ambulancezorg', 'system'),
    ('VTH_SECTOR', 'Sectoren VTH', 'system'),
    ('VTH_SECTOR_ADVIES_EN_MELDING', 'Afdelingen VTH Advies en melding', 'system'),
    ('VTH_SECTOR_ONDERZOEK', 'Afdelingen VTH Onderzoek', 'system'),
    ('VTH_SECTOR_VERVOLG', 'Afdelingen VTH Vervolg', 'system'),
    ('DIENSTVERLENINGSPRINCIPES', 'Dienstverleningsprincipes', 'system'),
    ('BEHOORLIJKHEIDSNORMEN', 'Behoorlijkheidsnormen', 'system'),
    ('KERNWAARDE_GOED_CONTACT', 'De overheid heeft goed contact met de burger', 'system'),
    ('KERNWAARDE_BURGER_CENTRAAL', 'De overheid zet burgers centraal en doet wat nodig is', 'system'),
    ('KERNWAARDE_VOOR_ALLE_BURGERS', 'De overheid werkt voor alle burgers', 'system'),
    ('KERNWAARDE_EERLIJK', 'De overheid is eerlijk', 'system'),
    ('OORDEEL', 'Oordeel', 'system'),
    ('PRODUCTEN', 'Producten', 'system'),
    ('THEMAS', 'Thema''s', 'system');

-- Diensten
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('DIENSTEN', 1, 'OCW', 'Onderwijs, Cultuur en Welzijn (OCW)', 'system'),
    ('DIENSTEN', 2, 'SZW', 'Sociale Zaken en Werkgelegenheid (SZW)', 'system'),
    ('DIENSTEN', 3, 'DPZ', 'Publiekszaken (DPZ)', 'system'),
    ('DIENSTEN', 4, 'DSB', 'Stadsbeheer (DSB)', 'system'),
    ('DIENSTEN', 5, 'DSO', 'Stedelijke Ontwikkeling (DSO)', 'system'),
    ('DIENSTEN', 6, 'DBV', 'Bedrijfsvoering (DBV)', 'system'),
    ('DIENSTEN', 7, 'BSD', 'Bestuursdienst (BSD)', 'system'),
    ('DIENSTEN', 8, 'GGD', 'GGD Haaglanden (GGD)', 'system'),
    ('DIENSTEN', 9, 'VTH', 'Veilig Thuis Haaglanden (VTH)', 'system');

-- Autorisatiegroepen OCW
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('AUTORISATIEGROEPEN_OCW', 1, 'AUTORISATIEGROEPEN_OCW_ALGEMEEN', 'OCW algemeen', 'system'),
    ('AUTORISATIEGROEPEN_OCW', 2, 'AUTORISATIEGROEPEN_OCW_JGZ_JEUGDGEZONDHEIDSZORG', 'OCW Jeugdgezondheidszorg (JGZ)', 'system'),
    ('AUTORISATIEGROEPEN_OCW', 3, 'AUTORISATIEGROEPEN_OCW_JEUGDHULP', 'OCW Jeugdhulp', 'system');

-- Autorisatiegroepen SZW
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('AUTORISATIEGROEPEN_SZW', 1, 'AUTORISATIEGROEPEN_SZW_ALGEMEEN', 'SZW algemeen', 'system');

-- Autorisatiegroepen DPZ
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('AUTORISATIEGROEPEN_DPZ', 1, 'AUTORISATIEGROEPEN_DPZ_ALGEMEEN', 'DPZ algemeen', 'system');

-- Autorisatiegroepen DSB
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('AUTORISATIEGROEPEN_DSB', 1, 'AUTORISATIEGROEPEN_DSB_ALGEMEEN', 'DSB algemeen', 'system');

-- Autorisatiegroepen DSO
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('AUTORISATIEGROEPEN_DSO', 1, 'AUTORISATIEGROEPEN_DSO_ALGEMEEN', 'DSO algemeen', 'system');

-- Autorisatiegroepen DBV
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('AUTORISATIEGROEPEN_DBV', 1, 'AUTORISATIEGROEPEN_DBV_ALGEMEEN', 'DBV algemeen', 'system');

-- Autorisatiegroepen BSD
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('AUTORISATIEGROEPEN_BSD', 1, 'AUTORISATIEGROEPEN_BSD_ALGEMEEN', 'BSD algemeen', 'system');

-- Autorisatiegroepen GGD
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('AUTORISATIEGROEPEN_GGD', 1, 'AUTORISATIEGROEPEN_GGD_ALGEMEEN', 'GGD algemeen', 'system');

-- Autorisatiegroepen VTH
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('AUTORISATIEGROEPEN_VTH', 1, 'AUTORISATIEGROEPEN_VTH_ALGEMEEN', 'VTH algemeen', 'system');

-- Sectoren OCW
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('OCW_SECTOR', 1, 'OCW_SECTOR_ONDERWIJS', 'Onderwijs', 'system'),
    ('OCW_SECTOR', 2, 'OCW_SECTOR_JEUGD', 'Jeugd', 'system'),
    ('OCW_SECTOR', 3, 'OCW_SECTOR_WELZIJN', 'Welzijn', 'system'),
    ('OCW_SECTOR', 4, 'OCW_SECTOR_CULTUUR', 'Cultuur', 'system'),
    ('OCW_SECTOR', 5, 'OCW_SECTOR_SPORT', 'Sport', 'system');

-- Afdelingen OCW Onderwijs
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('OCW_SECTOR_ONDERWIJS', 1, 'OCW_ONDERWIJS_LEERLINGENVERVOER', 'Leerlingenvervoer', 'system'),
    ('OCW_SECTOR_ONDERWIJS', 2, 'OCW_ONDERWIJS_LEERPLICHT', 'Leerplicht', 'system'),
    ('OCW_SECTOR_ONDERWIJS', 3, 'OCW_ONDERWIJS_ONDERWIJSHUISVESTING', 'Onderwijshuisvesting', 'system');

-- Afdelingen OCW Jeugd
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('OCW_SECTOR_JEUGD', 1, 'OCW_JEUGD_JEUGDHULP', 'Jeugdhulp', 'system'),
    ('OCW_SECTOR_JEUGD', 2, 'OCW_JEUGD_JEUGDGEZONDHEIDSZORG', 'Jeugdgezondheidszorg', 'system'),
    ('OCW_SECTOR_JEUGD', 3, 'OCW_JEUGD_JEUGDBELEID', 'Jeugdbeleid', 'system');

-- Afdelingen OCW Welzijn
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('OCW_SECTOR_WELZIJN', 1, 'OCW_WELZIJN_WELZIJN_EN_WIJKZAKEN', 'Welzijn en wijkzaken', 'system'),
    ('OCW_SECTOR_WELZIJN', 2, 'OCW_WELZIJN_OUDEREN', 'Ouderen', 'system'),
    ('OCW_SECTOR_WELZIJN', 3, 'OCW_WELZIJN_MAATSCHAPPELIJKE_OPVANG', 'Maatschappelijke opvang', 'system');

-- Afdelingen OCW Cultuur
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('OCW_SECTOR_CULTUUR', 1, 'OCW_CULTUUR_KUNST_EN_CULTUUR', 'Kunst en cultuur', 'system'),
    ('OCW_SECTOR_CULTUUR', 2, 'OCW_CULTUUR_BIBLIOTHEEK', 'Bibliotheek', 'system');

-- Afdelingen OCW Sport
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('OCW_SECTOR_SPORT', 1, 'OCW_SPORT_SPORTACCOMMODATIES', 'Sportaccommodaties', 'system'),
    ('OCW_SECTOR_SPORT', 2, 'OCW_SPORT_SPORTSTIMULERING', 'Sportstimulering', 'system');

-- Sectoren SZW
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('SZW_SECTOR', 1, 'SZW_SECTOR_WERK_EN_INKOMEN', 'Werk en Inkomen', 'system'),
    ('SZW_SECTOR', 2, 'SZW_SECTOR_ZORG', 'Zorg', 'system'),
    ('SZW_SECTOR', 3, 'SZW_SECTOR_SCHULDEN', 'Schulden', 'system'),
    ('SZW_SECTOR', 4, 'SZW_SECTOR_PARTICIPATIE', 'Participatie', 'system');

-- Afdelingen SZW Werk en Inkomen
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('SZW_SECTOR_WERK_EN_INKOMEN', 1, 'SZW_WERK_EN_INKOMEN_UITKERINGEN', 'Uitkeringen', 'system'),
    ('SZW_SECTOR_WERK_EN_INKOMEN', 2, 'SZW_WERK_EN_INKOMEN_WERKGEVERSSERVICEPUNT', 'Werkgeversservicepunt', 'system'),
    ('SZW_SECTOR_WERK_EN_INKOMEN', 3, 'SZW_WERK_EN_INKOMEN_RE_INTEGRATIE', 'Re-integratie', 'system');

-- Afdelingen SZW Zorg
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('SZW_SECTOR_ZORG', 1, 'SZW_ZORG_WMO_VOORZIENINGEN', 'Wmo-voorzieningen', 'system'),
    ('SZW_SECTOR_ZORG', 2, 'SZW_ZORG_HULPMIDDELEN', 'Hulpmiddelen', 'system'),
    ('SZW_SECTOR_ZORG', 3, 'SZW_ZORG_HUISHOUDELIJKE_ONDERSTEUNING', 'Huishoudelijke ondersteuning', 'system');

-- Afdelingen SZW Schulden
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('SZW_SECTOR_SCHULDEN', 1, 'SZW_SCHULDEN_SCHULDHULPVERLENING', 'Schuldhulpverlening', 'system'),
    ('SZW_SECTOR_SCHULDEN', 2, 'SZW_SCHULDEN_BIJZONDERE_BIJSTAND', 'Bijzondere bijstand', 'system');

-- Afdelingen SZW Participatie
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('SZW_SECTOR_PARTICIPATIE', 1, 'SZW_PARTICIPATIE_INBURGERING', 'Inburgering', 'system'),
    ('SZW_SECTOR_PARTICIPATIE', 2, 'SZW_PARTICIPATIE_TAAL', 'Taal', 'system');

-- Sectoren DPZ
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('DPZ_SECTOR', 1, 'DPZ_SECTOR_BURGERZAKEN', 'Burgerzaken', 'system'),
    ('DPZ_SECTOR', 2, 'DPZ_SECTOR_BELASTINGEN', 'Belastingen', 'system'),
    ('DPZ_SECTOR', 3, 'DPZ_SECTOR_PARKEREN', 'Parkeren', 'system'),
    ('DPZ_SECTOR', 4, 'DPZ_SECTOR_KLANTCONTACT', 'Klantcontact', 'system');

-- Afdelingen DPZ Burgerzaken
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('DPZ_SECTOR_BURGERZAKEN', 1, 'DPZ_BURGERZAKEN_REISDOCUMENTEN', 'Reisdocumenten', 'system'),
    ('DPZ_SECTOR_BURGERZAKEN', 2, 'DPZ_BURGERZAKEN_BASISREGISTRATIE_PERSONEN', 'Basisregistratie personen', 'system'),
    ('DPZ_SECTOR_BURGERZAKEN', 3, 'DPZ_BURGERZAKEN_BURGERLIJKE_STAND', 'Burgerlijke stand', 'system');

-- Afdelingen DPZ Belastingen
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('DPZ_SECTOR_BELASTINGEN', 1, 'DPZ_BELASTINGEN_HEFFING', 'Heffing', 'system'),
    ('DPZ_SECTOR_BELASTINGEN', 2, 'DPZ_BELASTINGEN_INVORDERING', 'Invordering', 'system'),
    ('DPZ_SECTOR_BELASTINGEN', 3, 'DPZ_BELASTINGEN_KWIJTSCHELDING', 'Kwijtschelding', 'system');

-- Afdelingen DPZ Parkeren
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('DPZ_SECTOR_PARKEREN', 1, 'DPZ_PARKEREN_PARKEERVERGUNNINGEN', 'Parkeervergunningen', 'system'),
    ('DPZ_SECTOR_PARKEREN', 2, 'DPZ_PARKEREN_PARKEERHANDHAVING', 'Parkeerhandhaving', 'system');

-- Afdelingen DPZ Klantcontact
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('DPZ_SECTOR_KLANTCONTACT', 1, 'DPZ_KLANTCONTACT_KLANTCONTACTCENTRUM', 'Klantcontactcentrum', 'system'),
    ('DPZ_SECTOR_KLANTCONTACT', 2, 'DPZ_KLANTCONTACT_STADSDEELKANTOREN', 'Stadsdeelkantoren', 'system');

-- Sectoren DSB
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('DSB_SECTOR', 1, 'DSB_SECTOR_AFVAL', 'Afval', 'system'),
    ('DSB_SECTOR', 2, 'DSB_SECTOR_OPENBARE_RUIMTE', 'Openbare ruimte', 'system'),
    ('DSB_SECTOR', 3, 'DSB_SECTOR_GROEN', 'Groen', 'system'),
    ('DSB_SECTOR', 4, 'DSB_SECTOR_HANDHAVING', 'Handhaving', 'system');

-- Afdelingen DSB Afval
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('DSB_SECTOR_AFVAL', 1, 'DSB_AFVAL_HUISHOUDELIJK_AFVAL', 'Huishoudelijk afval', 'system'),
    ('DSB_SECTOR_AFVAL', 2, 'DSB_AFVAL_GROFVUIL', 'Grofvuil', 'system'),
    ('DSB_SECTOR_AFVAL', 3, 'DSB_AFVAL_ONDERGRONDSE_CONTAINERS', 'Ondergrondse containers', 'system');

-- Afdelingen DSB Openbare ruimte
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('DSB_SECTOR_OPENBARE_RUIMTE', 1, 'DSB_OPENBARE_RUIMTE_STRATEN_EN_PLEINEN', 'Straten en pleinen', 'system'),
    ('DSB_SECTOR_OPENBARE_RUIMTE', 2, 'DSB_OPENBARE_RUIMTE_OPENBARE_VERLICHTING', 'Openbare verlichting', 'system'),
    ('DSB_SECTOR_OPENBARE_RUIMTE', 3, 'DSB_OPENBARE_RUIMTE_SPEELPLAATSEN', 'Speelplaatsen', 'system');

-- Afdelingen DSB Groen
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('DSB_SECTOR_GROEN', 1, 'DSB_GROEN_BOMEN', 'Bomen', 'system'),
    ('DSB_SECTOR_GROEN', 2, 'DSB_GROEN_PARKEN', 'Parken', 'system');

-- Afdelingen DSB Handhaving
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('DSB_SECTOR_HANDHAVING', 1, 'DSB_HANDHAVING_TOEZICHT_OPENBARE_RUIMTE', 'Toezicht openbare ruimte', 'system'),
    ('DSB_SECTOR_HANDHAVING', 2, 'DSB_HANDHAVING_BOAS', 'Boa''s', 'system');

-- Sectoren DSO
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('DSO_SECTOR', 1, 'DSO_SECTOR_RUIMTELIJKE_ORDENING', 'Ruimtelijke ordening', 'system'),
    ('DSO_SECTOR', 2, 'DSO_SECTOR_VERGUNNINGEN', 'Vergunningen', 'system'),
    ('DSO_SECTOR', 3, 'DSO_SECTOR_MOBILITEIT', 'Mobiliteit', 'system'),
    ('DSO_SECTOR', 4, 'DSO_SECTOR_WONEN', 'Wonen', 'system');

-- Afdelingen DSO Ruimtelijke ordening
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('DSO_SECTOR_RUIMTELIJKE_ORDENING', 1, 'DSO_RUIMTELIJKE_ORDENING_OMGEVINGSPLAN', 'Omgevingsplan', 'system'),
    ('DSO_SECTOR_RUIMTELIJKE_ORDENING', 2, 'DSO_RUIMTELIJKE_ORDENING_GEBIEDSONTWIKKELING', 'Gebiedsontwikkeling', 'system');

-- Afdelingen DSO Vergunningen
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('DSO_SECTOR_VERGUNNINGEN', 1, 'DSO_VERGUNNINGEN_OMGEVINGSVERGUNNINGEN', 'Omgevingsvergunningen', 'system'),
    ('DSO_SECTOR_VERGUNNINGEN', 2, 'DSO_VERGUNNINGEN_TOEZICHT_BOUW', 'Toezicht bouw', 'system');

-- Afdelingen DSO Mobiliteit
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('DSO_SECTOR_MOBILITEIT', 1, 'DSO_MOBILITEIT_VERKEER', 'Verkeer', 'system'),
    ('DSO_SECTOR_MOBILITEIT', 2, 'DSO_MOBILITEIT_FIETS_EN_VOETGANGER', 'Fiets en voetganger', 'system'),
    ('DSO_SECTOR_MOBILITEIT', 3, 'DSO_MOBILITEIT_OPENBAAR_VERVOER', 'Openbaar vervoer', 'system');

-- Afdelingen DSO Wonen
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('DSO_SECTOR_WONEN', 1, 'DSO_WONEN_WONINGZOEKENDEN', 'Woningzoekenden', 'system'),
    ('DSO_SECTOR_WONEN', 2, 'DSO_WONEN_HUISVESTINGSVERGUNNINGEN', 'Huisvestingsvergunningen', 'system');

-- Sectoren DBV
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('DBV_SECTOR', 1, 'DBV_SECTOR_ICT', 'ICT', 'system'),
    ('DBV_SECTOR', 2, 'DBV_SECTOR_FINANCIEN', 'Financiën', 'system'),
    ('DBV_SECTOR', 3, 'DBV_SECTOR_INKOOP', 'Inkoop', 'system'),
    ('DBV_SECTOR', 4, 'DBV_SECTOR_HR', 'HR', 'system');

-- Afdelingen DBV ICT
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('DBV_SECTOR_ICT', 1, 'DBV_ICT_SERVICEDESK', 'Servicedesk', 'system'),
    ('DBV_SECTOR_ICT', 2, 'DBV_ICT_INFORMATIEBEVEILIGING', 'Informatiebeveiliging', 'system');

-- Afdelingen DBV Financiën
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('DBV_SECTOR_FINANCIEN', 1, 'DBV_FINANCIEN_CREDITEURENADMINISTRATIE', 'Crediteurenadministratie', 'system'),
    ('DBV_SECTOR_FINANCIEN', 2, 'DBV_FINANCIEN_DEBITEURENADMINISTRATIE', 'Debiteurenadministratie', 'system');

-- Afdelingen DBV Inkoop
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('DBV_SECTOR_INKOOP', 1, 'DBV_INKOOP_INKOOP_EN_AANBESTEDING', 'Inkoop en aanbesteding', 'system'),
    ('DBV_SECTOR_INKOOP', 2, 'DBV_INKOOP_CONTRACTMANAGEMENT', 'Contractmanagement', 'system');

-- Afdelingen DBV HR
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('DBV_SECTOR_HR', 1, 'DBV_HR_PERSONEELSZAKEN', 'Personeelszaken', 'system'),
    ('DBV_SECTOR_HR', 2, 'DBV_HR_ARBO', 'Arbo', 'system');

-- Sectoren BSD
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('BSD_SECTOR', 1, 'BSD_SECTOR_BESTUURSZAKEN', 'Bestuurszaken', 'system'),
    ('BSD_SECTOR', 2, 'BSD_SECTOR_COMMUNICATIE', 'Communicatie', 'system'),
    ('BSD_SECTOR', 3, 'BSD_SECTOR_JURIDISCHE_ZAKEN', 'Juridische zaken', 'system');

-- Afdelingen BSD Bestuurszaken
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('BSD_SECTOR_BESTUURSZAKEN', 1, 'BSD_BESTUURSZAKEN_BESTUURSONDERSTEUNING', 'Bestuursondersteuning', 'system'),
    ('BSD_SECTOR_BESTUURSZAKEN', 2, 'BSD_BESTUURSZAKEN_KABINET', 'Kabinet', 'system');

-- Afdelingen BSD Communicatie
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('BSD_SECTOR_COMMUNICATIE', 1, 'BSD_COMMUNICATIE_PERS_EN_WOORDVOERING', 'Pers en woordvoering', 'system'),
    ('BSD_SECTOR_COMMUNICATIE', 2, 'BSD_COMMUNICATIE_ONLINE', 'Online', 'system');

-- Afdelingen BSD Juridische zaken
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('BSD_SECTOR_JURIDISCHE_ZAKEN', 1, 'BSD_JURIDISCHE_ZAKEN_BEZWAAR_EN_BEROEP', 'Bezwaar en beroep', 'system'),
    ('BSD_SECTOR_JURIDISCHE_ZAKEN', 2, 'BSD_JURIDISCHE_ZAKEN_AANSPRAKELIJKHEID', 'Aansprakelijkheid', 'system');

-- Sectoren GGD
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('GGD_SECTOR', 1, 'GGD_SECTOR_INFECTIEZIEKTEN', 'Infectieziekten', 'system'),
    ('GGD_SECTOR', 2, 'GGD_SECTOR_MILIEU_EN_GEZONDHEID', 'Milieu en gezondheid', 'system'),
    ('GGD_SECTOR', 3, 'GGD_SECTOR_FORENSISCHE_GENEESKUNDE', 'Forensische geneeskunde', 'system'),
    ('GGD_SECTOR', 4, 'GGD_SECTOR_AMBULANCEZORG', 'Ambulancezorg', 'system');

-- Afdelingen GGD Infectieziekten
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('GGD_SECTOR_INFECTIEZIEKTEN', 1, 'GGD_INFECTIEZIEKTEN_INFECTIEZIEKTEBESTRIJDING', 'Infectieziektebestrijding', 'system'),
    ('GGD_SECTOR_INFECTIEZIEKTEN', 2, 'GGD_INFECTIEZIEKTEN_TUBERCULOSEBESTRIJDING', 'Tuberculosebestrijding', 'system'),
    ('GGD_SECTOR_INFECTIEZIEKTEN', 3, 'GGD_INFECTIEZIEKTEN_SEKSUELE_GEZONDHEID', 'Seksuele gezondheid', 'system');

-- Afdelingen GGD Milieu en gezondheid
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('GGD_SECTOR_MILIEU_EN_GEZONDHEID', 1, 'GGD_MILIEU_EN_GEZONDHEID_MEDISCHE_MILIEUKUNDE', 'Medische milieukunde', 'system'),
    ('GGD_SECTOR_MILIEU_EN_GEZONDHEID', 2, 'GGD_MILIEU_EN_GEZONDHEID_HYGIENE_EN_INSPECTIE', 'Hygiëne en inspectie', 'system');

-- Afdelingen GGD Forensische geneeskunde
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('GGD_SECTOR_FORENSISCHE_GENEESKUNDE', 1, 'GGD_FORENSISCHE_GENEESKUNDE_LIJKSCHOUW', 'Lijkschouw', 'system'),
    ('GGD_SECTOR_FORENSISCHE_GENEESKUNDE', 2, 'GGD_FORENSISCHE_GENEESKUNDE_ARRESTANTENZORG', 'Arrestantenzorg', 'system');

-- Afdelingen GGD Ambulancezorg
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('GGD_SECTOR_AMBULANCEZORG', 1, 'GGD_AMBULANCEZORG_MELDKAMER_AMBULANCEZORG', 'Meldkamer ambulancezorg', 'system'),
    ('GGD_SECTOR_AMBULANCEZORG', 2, 'GGD_AMBULANCEZORG_AMBULANCEDIENST', 'Ambulancedienst', 'system');

-- Sectoren VTH
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('VTH_SECTOR', 1, 'VTH_SECTOR_ADVIES_EN_MELDING', 'Advies en melding', 'system'),
    ('VTH_SECTOR', 2, 'VTH_SECTOR_ONDERZOEK', 'Onderzoek', 'system'),
    ('VTH_SECTOR', 3, 'VTH_SECTOR_VERVOLG', 'Vervolg', 'system');

-- Afdelingen VTH Advies en melding
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('VTH_SECTOR_ADVIES_EN_MELDING', 1, 'VTH_ADVIES_EN_MELDING_ADVIESLIJN', 'Advieslijn', 'system'),
    ('VTH_SECTOR_ADVIES_EN_MELDING', 2, 'VTH_ADVIES_EN_MELDING_MELDINGEN', 'Meldingen', 'system');

-- Afdelingen VTH Onderzoek
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('VTH_SECTOR_ONDERZOEK', 1, 'VTH_ONDERZOEK_TRIAGE', 'Triage', 'system'),
    ('VTH_SECTOR_ONDERZOEK', 2, 'VTH_ONDERZOEK_ONDERZOEK', 'Onderzoek', 'system');

-- Afdelingen VTH Vervolg
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('VTH_SECTOR_VERVOLG', 1, 'VTH_VERVOLG_MONITORING', 'Monitoring', 'system'),
    ('VTH_SECTOR_VERVOLG', 2, 'VTH_VERVOLG_OVERDRACHT', 'Overdracht', 'system');

-- Dienstverleningsprincipes
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('DIENSTVERLENINGSPRINCIPES', 1, 'KERNWAARDE_GOED_CONTACT', 'De overheid heeft goed contact met de burger', 'system'),
    ('DIENSTVERLENINGSPRINCIPES', 2, 'KERNWAARDE_BURGER_CENTRAAL', 'De overheid zet burgers centraal en doet wat nodig is', 'system'),
    ('DIENSTVERLENINGSPRINCIPES', 3, 'KERNWAARDE_VOOR_ALLE_BURGERS', 'De overheid werkt voor alle burgers', 'system'),
    ('DIENSTVERLENINGSPRINCIPES', 4, 'KERNWAARDE_EERLIJK', 'De overheid is eerlijk', 'system');

-- Behoorlijkheidsnormen
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('BEHOORLIJKHEIDSNORMEN', 1, 'KERNWAARDE_GOED_CONTACT', 'De overheid heeft goed contact met de burger', 'system'),
    ('BEHOORLIJKHEIDSNORMEN', 2, 'KERNWAARDE_BURGER_CENTRAAL', 'De overheid zet burgers centraal en doet wat nodig is', 'system'),
    ('BEHOORLIJKHEIDSNORMEN', 3, 'KERNWAARDE_VOOR_ALLE_BURGERS', 'De overheid werkt voor alle burgers', 'system'),
    ('BEHOORLIJKHEIDSNORMEN', 4, 'KERNWAARDE_EERLIJK', 'De overheid is eerlijk', 'system');

-- De overheid heeft goed contact met de burger
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('KERNWAARDE_GOED_CONTACT', 1, 'LUISTEREN_NAAR_BURGERS', 'Luisteren naar burgers', 'system'),
    ('KERNWAARDE_GOED_CONTACT', 2, 'BURGERS_BETREKKEN', 'Burgers betrekken', 'system'),
    ('KERNWAARDE_GOED_CONTACT', 3, 'GOEDE_VOORBEREIDING', 'Goede voorbereiding', 'system'),
    ('KERNWAARDE_GOED_CONTACT', 4, 'RESPECTVOL', 'Respectvol', 'system'),
    ('KERNWAARDE_GOED_CONTACT', 5, 'DE_ESCALATIE', 'De-escalatie', 'system');

-- De overheid zet burgers centraal en doet wat nodig is
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('KERNWAARDE_BURGER_CENTRAAL', 1, 'MENSENRECHTEN_RESPECTEREN', 'Mensenrechten respecteren', 'system'),
    ('KERNWAARDE_BURGER_CENTRAAL', 2, 'MAATWERK', 'Maatwerk', 'system'),
    ('KERNWAARDE_BURGER_CENTRAAL', 3, 'EVENREDIGHEID', 'Evenredigheid', 'system'),
    ('KERNWAARDE_BURGER_CENTRAAL', 4, 'BIJZONDERE_ZORG', 'Bijzondere zorg', 'system'),
    ('KERNWAARDE_BURGER_CENTRAAL', 5, 'COULANTE_OPSTELLING', 'Coulante opstelling', 'system');

-- De overheid werkt voor alle burgers
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('KERNWAARDE_VOOR_ALLE_BURGERS', 1, 'REGIEROL', 'Regierol', 'system'),
    ('KERNWAARDE_VOOR_ALLE_BURGERS', 2, 'GOEDE_INFORMATIEVERSTREKKING', 'Goede informatieverstrekking', 'system'),
    ('KERNWAARDE_VOOR_ALLE_BURGERS', 3, 'GOEDE_MOTIVERING', 'Goede motivering', 'system'),
    ('KERNWAARDE_VOOR_ALLE_BURGERS', 4, 'VOORTVARENDHEID', 'Voortvarendheid', 'system'),
    ('KERNWAARDE_VOOR_ALLE_BURGERS', 5, 'BETROUWBAARHEID', 'Betrouwbaarheid', 'system'),
    ('KERNWAARDE_VOOR_ALLE_BURGERS', 6, 'TOEGANKELIJKHEID', 'Toegankelijkheid', 'system');

-- De overheid is eerlijk
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('KERNWAARDE_EERLIJK', 1, 'EERLIJKE_PROCESKANSEN', 'Eerlijke proceskansen', 'system'),
    ('KERNWAARDE_EERLIJK', 2, 'INTEGRITEIT', 'Integriteit', 'system'),
    ('KERNWAARDE_EERLIJK', 3, 'ONPARTIJDIGHEID', 'Onpartijdigheid', 'system'),
    ('KERNWAARDE_EERLIJK', 4, 'TRANSPARANTIE', 'Transparantie', 'system');

-- Oordeel
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('OORDEEL', 1, 'GEGROND', 'Gegrond', 'system'),
    ('OORDEEL', 2, 'DEELS_GEGROND', 'Deels gegrond', 'system'),
    ('OORDEEL', 3, 'ONGEGROND', 'Ongegrond', 'system'),
    ('OORDEEL', 4, 'GEEN_OORDEEL', 'Geen oordeel', 'system');

-- Producten
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('PRODUCTEN', 1, 'PASPOORT_EN_IDENTITEITSKAART', 'Paspoort en identiteitskaart', 'system'),
    ('PRODUCTEN', 2, 'RIJBEWIJS', 'Rijbewijs', 'system'),
    ('PRODUCTEN', 3, 'VERHUIZING_DOORGEVEN', 'Verhuizing doorgeven', 'system'),
    ('PRODUCTEN', 4, 'HUWELIJK_EN_PARTNERSCHAP', 'Huwelijk en partnerschap', 'system'),
    ('PRODUCTEN', 5, 'PARKEERVERGUNNING', 'Parkeervergunning', 'system'),
    ('PRODUCTEN', 6, 'GEMEENTELIJKE_BELASTINGEN', 'Gemeentelijke belastingen', 'system'),
    ('PRODUCTEN', 7, 'KWIJTSCHELDING', 'Kwijtschelding', 'system'),
    ('PRODUCTEN', 8, 'BIJSTANDSUITKERING', 'Bijstandsuitkering', 'system'),
    ('PRODUCTEN', 9, 'WMO_VOORZIENING', 'Wmo-voorziening', 'system'),
    ('PRODUCTEN', 10, 'SCHULDHULPVERLENING', 'Schuldhulpverlening', 'system'),
    ('PRODUCTEN', 11, 'OMGEVINGSVERGUNNING', 'Omgevingsvergunning', 'system'),
    ('PRODUCTEN', 12, 'AFVALINZAMELING', 'Afvalinzameling', 'system'),
    ('PRODUCTEN', 13, 'GROFVUIL', 'Grofvuil', 'system'),
    ('PRODUCTEN', 14, 'MELDING_OPENBARE_RUIMTE', 'Melding openbare ruimte', 'system'),
    ('PRODUCTEN', 15, 'LEERLINGENVERVOER', 'Leerlingenvervoer', 'system'),
    ('PRODUCTEN', 16, 'JEUGDHULP', 'Jeugdhulp', 'system'),
    ('PRODUCTEN', 17, 'SUBSIDIE', 'Subsidie', 'system');

-- Thema's
INSERT INTO choice_field_values (choice_field_name, sort_order, name, value, created_by) VALUES
    ('THEMAS', 1, 'BEJEGENING', 'Bejegening', 'system'),
    ('THEMAS', 2, 'BEREIKBAARHEID', 'Bereikbaarheid', 'system'),
    ('THEMAS', 3, 'INFORMATIEVOORZIENING', 'Informatievoorziening', 'system'),
    ('THEMAS', 4, 'AFHANDELINGSTERMIJN', 'Afhandelingstermijn', 'system'),
    ('THEMAS', 5, 'KWALITEIT_DIENSTVERLENING', 'Kwaliteit dienstverlening', 'system'),
    ('THEMAS', 6, 'ONJUISTE_BESLISSING', 'Onjuiste beslissing', 'system'),
    ('THEMAS', 7, 'BELEID_EN_REGELGEVING', 'Beleid en regelgeving', 'system'),
    ('THEMAS', 8, 'PRIVACY', 'Privacy', 'system');
