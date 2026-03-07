INSERT INTO boxes (resident_name, address, contact_number)
VALUES
    ('Mdm Tan Ah Lian', 'Blk 101 Ang Mo Kio Ave 3, #09-22', '+65-9000-1001'),
    ('Mr Gopal Krishnan', 'Blk 77 Jurong West St 52, #03-11', '+65-9000-2002');

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
      '????,?????',
      'I have fallen and cannot get up.',
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
    );