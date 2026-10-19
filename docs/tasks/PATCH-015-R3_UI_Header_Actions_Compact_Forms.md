# PATCH-015-R3 UI Header Actions Compact Forms

**Projekt:** MSDS Manager  
**Typ:** UI PATCH  
**Status:** TO IMPLEMENT  
**Zakres:** tylko UI / układ / stylizacja  
**Bez zmian:** Domain, Application, DB schema, migracje, logika biznesowa

## Cel

Dopracować ergonomię `Karty Produktu`, ograniczyć zajętość pionową, lepiej wykorzystać szerokość ekranu i ujednolicić akcje.

## Wymagania

1. Na ekranie `Karta Produktu` przenieść `Pobierz SDS` z `SDS i BHP` do górnej listwy akcji pod tytułem produktu. Listwa zawiera `Korekta danych identyfikacyjnych`, `Dodaj nową rewizję SDS`, `Pobierz SDS`, `Więcej akcji`.
2. W formularzu `Dodaj miejsce stosowania` umieścić `Przypisz lokalizację` i `Anuluj` w jednej linii; oba jako przyciski kolorowe. `Dodaj miejsce` pozostaje pod tabelą.
3. `Edytuj` jest po prawej stronie tytułu `Dane administracyjne`.
4. Dane administracyjne w odczycie: lewa kolumna `Opis użycia`, `Typ odpadu`; prawa `Ograniczenia użycia`, `Kod odpadu`.
5. W edycji `Zapisz dane administracyjne` i `Anuluj` są w jednej linii i wizualnie spójne.
6. Kolory: primary wypełniony akcentem, secondary łagodny lub outline, neutral szary, danger czerwony tylko dla akcji destrukcyjnych.

## Ograniczenia

- Bez zmian routingu, logiki formularzy, danych testowych i logiki SDS/BHP.
- Bez nowych zależności, jeśli nie są konieczne.

## Kryteria akceptacji

- `Pobierz SDS` w górnym pasku akcji.
- Przyciski formularza dodawania miejsca w jednej linii.
- `Edytuj` w nagłówku danych administracyjnych.
- Dane administracyjne w dwóch kolumnach.
- `Zapisz` / `Anuluj` w jednej linii.
- Spójny, stonowany system kolorów przycisków.
- Ekran bardziej zwarty i wymagający mniej przewijania.

## Oczekiwany rezultat

- Raport: `PATCH-015-R3_REPORT.md`.
- Zrzuty porównawcze: `Produkty` i `Karta Produktu`.
