INSERT INTO boxes (resident_name, address, contact_number)
VALUES
    ('Mdm Tan Ah Lian', 'Blk 101 Ang Mo Kio Ave 3, #09-22', '+65-9000-1001'),
    ('Mr Gopal Krishnan', 'Blk 77 Jurong West St 52, #03-11', '+65-9000-2002')
ON CONFLICT DO NOTHING;

INSERT INTO alerts (
    box_id,
    detected_language,
    transcript,
    english_translation,
    severity,
    status,
    is_simulated_ai
)
VALUES
    (
      1,
      'Cantonese',
      'I fell down and cannot stand up.',
      'I fell down and cannot stand up.',
      'EMERGENCY',
      'open',
      TRUE
    ),
    (
      2,
      'English',
      'I need help with my medicine timing.',
      'I need help with my medicine timing.',
      'ROUTINE',
      'open',
      TRUE
    )
ON CONFLICT DO NOTHING;