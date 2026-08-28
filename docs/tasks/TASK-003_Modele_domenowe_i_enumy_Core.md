# TASK-003 — Modele domenowe i enumy Core

**Projekt:** MSDS Manager
**Task ID:** TASK-003
**Sprint:** SPRINT-001 — Foundation / Core Skeleton
**Status wejściowy:** READY
**Wykonawca:** Codex OpenAI
**Nadzór:** Cerberus — Agent Architekt
**Akceptacja końcowa:** Architekt Operacyjny

## 1. Cel

Zaimplementować czysty, niezależny od infrastruktury model domenowy Core MSDS Manager oraz wymagane enumy zgodnie z zatwierdzonym CORE-001 i BDR-001..005.

TASK-003 nie tworzy modeli SQLAlchemy, tabel PostgreSQL, migracji Alembic, repozytoriów, UI, parsera PDF, AI ani REACH.

## 2. Warunek wejścia

TASK-002 jest zaakceptowany. PostgreSQL i konfiguracja działają, lecz baza nadal nie posiada tabel aplikacyjnych, a Alembic nie posiada rewizji domenowych.

## 3. Obowiązujące źródła

Przede wszystkim:
- CORE-001 v1.0-approved,
- BDR-001, BDR-002, BDR-003, BDR-004, BDR-005 v1.0-approved,
- TDR-001, TDR-002, TDR-003,
- PDP-001, ROADMAP-001, Konstytucja i AGENTS.md.

Jeżeli źródła są niejednoznaczne lub sprzeczne, nie zgaduj — zastosuj STOP.

## 4. Granica architektoniczna

Kod TASK-003 należy do `app/domain/`.

Domena nie może importować SQLAlchemy, psycopg, Alembic, Streamlit, `app.infrastructure` ani konfiguracji `.env`.

Preferuj standardową bibliotekę Pythona, proste typy i minimalną złożoność.

## 5. Enumy

Utwórz co najmniej:

- `ProductUsageStatus`: `PENDING_APPROVAL`, `ACTIVE`, `REJECTED`, `INACTIVE`
- `SdsDocumentStatus`: `CURRENT`, `ARCHIVED`
- `FileAvailabilityStatus`: `AVAILABLE`, `MISSING`
- `BhpDecisionStatus`: `APPROVED`, `REJECTED` — bez `PENDING`
- `DecisionRecordStatus`: `CURRENT`, `SUPERSEDED`
- `SafetyInformationStatus`: `YES`, `NO`, `NO_DATA`, `NOT_APPLICABLE`
- `EvidenceType`: `EMAIL`, `DOCUMENT`, `PHOTO_SCAN`
- `EvidenceFileFormat`: `MSG`, `PDF`, `JPG`, `JPEG`, `PNG`

Nie dodawaj niezatwierdzonych wartości.

## 6. Modele domenowe

### Manufacturer
- `manufacturer_id`
- `manufacturer_name`

### Product
- `product_id`
- `product_name`
- `manufacturer_product_code`
- `manufacturer_id`
- `use_description`
- `use_restriction`
- `usage_status: ProductUsageStatus`

Nie modeluj dostawcy.

### UsageLocation
- `location_id`
- `location_name`
- `status`

Jeżeli zatwierdzone źródła nie definiują enumu dla `status`, nie wymyślaj jego wartości. Zastosuj prostą reprezentację albo STOP dla tego fragmentu, jeżeli konieczna byłaby nowa decyzja.

### ProductUsageLocation
- `product_id`
- `location_id`
- `quantity_value`
- `quantity_unit`

Nie modeluj magazynu ani ruchów materiałowych.

### SdsDocument
- `sds_id`
- `product_id`
- `original_filename`
- `relative_path`
- `issue_date` — opcjonalne
- `revision` — opcjonalne
- `document_status: SdsDocumentStatus`
- `registered_at`
- `file_status: FileAvailabilityStatus`

Model nie sprawdza filesystemu podczas konstrukcji.

### BhpDecision
- `decision_id`
- `product_id`
- `sds_id`
- `decision_status: BhpDecisionStatus`
- `notes` — opcjonalne
- `registered_at`
- `record_status: DecisionRecordStatus`
- `evidence_id`

Nie dodawaj `decided_by`, osobnego `decision_date` ani strukturalnego modelu warunków dopuszczenia.

### DecisionEvidence
Co najmniej:
- `evidence_id`
- `relative_path`
- `evidence_type: EvidenceType`
- `file_format: EvidenceFileFormat`
- `file_status: FileAvailabilityStatus`

Nie przechowuj binarnej zawartości dokumentu.

### SafetyProfile
Należy do konkretnego `sds_id`:
- `sds_id`
- `product_definition`
- `hazardous_classification_status`
- `clp_classification_text`
- `signal_word`
- `hazard_statements`
- `supplemental_hazard_statements`
- `pbt_status`
- `vpvb_status`
- `carcinogenicity_status`
- `germ_cell_mutagenicity_status`
- `reproductive_toxicity_status`
- `endocrine_section_2_status`
- `endocrine_section_11_status`
- `skin_sensitization_status`
- `respiratory_sensitization_status`
- `approved_at`
- `last_manual_edit_at` — opcjonalne, domyślnie `None`

Dla pól statusowych używaj `SafetyInformationStatus` zgodnie z BDR-005. Nie dodawaj confidence score, per-field provenance ani automatycznego rozstrzygania dwóch statusów endokrynnych.

### SdsComponent
- `component_id`
- `sds_id`
- `component_name`
- `cas_number`
- `ec_number`
- `reach_registration_number`
- `concentration_text`
- `classification_text`
- `hazard_statements`

Pola niewystępujące w SDS muszą umożliwiać reprezentację braku danych. Nie przenoś klasyfikacji składnika na SafetyProfile produktu.

## 7. Typy danych

Identyfikatory mają być jawne, ale TASK-003 nie projektuje strategii kluczy PostgreSQL.

Użyj standardowych typów dat/czasu. Dla `quantity_value` użyj typu bez utraty precyzji właściwej dla `float` (np. `Decimal`). Nie twórz systemu konwersji jednostek.

Dla kolekcji H-statements wybierz prostą deterministyczną reprezentację; nie twórz osobnej encji H-statement.

## 8. Reguła domenowa ilości

Zaimplementuj i przetestuj agregację sumarycznej ilości produktu dla fabryki:

- wejście: zbiór `ProductUsageLocation` jednego produktu,
- te same jednostki → suma,
- różne jednostki → jawna odmowa sumowania przez domenowy wyjątek,
- brak automatycznej konwersji `kg↔g`, `l↔ml`, `kg↔l`.

Reguły wymagające persistence, np. maksymalnie jeden CURRENT SDS lub CURRENT BHP decision, mają być na tym etapie reprezentowane przez model i enumy, ale nie muszą być jeszcze egzekwowane transakcyjnie.

## 9. Walidacja

Dodawaj tylko walidacje wynikające jednoznacznie ze źródeł. Nie twórz ogólnego frameworka walidacji ani nowych reguł biznesowych.

## 10. Struktura

Użyj istniejących katalogów:

```text
app/domain/
├── models/
├── enums/
├── rules/
└── exceptions/
```

Podział plików ma być czytelny, bez jednego monolitycznego pliku i bez niepotrzebnych mikroplików.

## 11. Testy

Dodaj testy jednostkowe bez PostgreSQL, `.env`, filesystemu, Streamlit i SQLAlchemy.

Pokryj co najmniej:
1. dokładne wartości enumów,
2. tworzenie modeli,
3. opcjonalność `issue_date` i `revision`,
4. `NO_DATA != NO`,
5. niezależność statusów endokrynnych,
6. brak `PENDING` w BhpDecisionStatus,
7. CURRENT/SUPERSEDED,
8. sumowanie jednej jednostki,
9. odmowę sumowania różnych jednostek,
10. brak konwersji jednostek,
11. brakujące dane SdsComponent,
12. `last_manual_edit_at is None`.

Uruchom wszystkie istniejące testy regresyjne.

## 12. Kontrole

Zaraportuj:
- brak importów SQLAlchemy/Streamlit/infrastructure w `app/domain`,
- brak ORM,
- brak migracji,
- `alembic history` nadal bez rewizji domenowej,
- brak tabel aplikacyjnych w PostgreSQL,
- brak nowych bibliotek w `pyproject.toml`.

## 13. Poza zakresem

Nie implementuj: ORM, tabel, migracji, repository/CRUD, UI, parsera PDF, OCR, AI/LLM, workflow ekstrakcji, tłumaczeń SDS, REACH, deduplikacji, magazynu, zakupów, dostawców, konwersji jednostek, pełnej Sekcji 11, confidence score ani automatycznej decyzji BHP.

## 14. Ochrona

Nie modyfikuj zatwierdzonych dokumentów governance/Core, `.env`, konfiguracji systemowego PostgreSQL ani PATH. Nie zapisuj sekretów.

## 15. STOP

Zatrzymaj problematyczny fragment, jeżeli:
- źródła są sprzeczne lub niejednoznaczne,
- potrzebny jest nowy ADR/BDR/TDR,
- konieczna byłaby zmiana Core,
- potrzebna jest nowa biblioteka,
- trzeba zgadywać enum/regułę,
- praca wchodzi w TASK-004.

Bezpieczne części mogą zostać wykonane, a wynik oznaczony `PARTIAL`.

## 16. Kryteria akceptacji

DONE wymaga:
- modeli i enumów w domenie,
- reguły agregacji ilości,
- jawnej odmowy sumowania różnych jednostek,
- niezależności domeny od infrastruktury/UI,
- braku ORM/migracji/tabel/nowych zależności,
- wszystkich testów zielonych,
- kompletnego raportu,
- zatrzymania po TASK-003.

## 17. Raport

Utwórz `docs/task_reports/TASK-003_REPORT.md` z:
- statusem `DONE`/`PARTIAL`/`BLOCKED`,
- zakresem wykonania,
- listą modeli i enumów,
- pełną listą zmienionych plików,
- poleceniami testowymi i wynikami,
- kontrolą architektury i bazy,
- odstępstwami,
- problemami wymagającymi decyzji,
- potwierdzeniem bezpieczeństwa Git i `.env`.

## 18. Zakończenie

Po TASK-003 zapisz raport, przedstaw podsumowanie użytkownikowi i zatrzymaj się. Nie rozpoczynaj TASK-004, nie twórz modeli SQLAlchemy ani migracji. Oczekuj na review Cerberusa.
