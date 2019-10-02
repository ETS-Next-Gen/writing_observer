reset: |
  DROP TABLE IF EXISTS USERS;
  DROP TABLE IF EXISTS WRITING_DELTAS;
  DROP TABLE IF EXISTS DOCUMENTS;
  DROP FUNCTION IF EXISTS insert_writing_delta;

init: |
  CREATE TABLE IF NOT EXISTS USERS (
         idx          SERIAL PRIMARY KEY,
         username     text UNIQUE,
         email        text,
         date_created timestamp NOT NULL DEFAULT NOW()
  );
  
  CREATE TABLE IF NOT EXISTS DOCUMENTS (
         idx       SERIAL PRIMARY KEY,
         docstring char(48) UNIQUE,
         date_created timestamp NOT NULL DEFAULT NOW()
  );
  
  CREATE TABLE IF NOT EXISTS WRITING_DELTAS (
         idx      SERIAL PRIMARY KEY,
         user_id  integer REFERENCES USERS (idx),  -- Who is editing?
         document integer REFERENCES DOCUMENTS (idx), -- Which document?
         date_created timestamp NOT NULL DEFAULT NOW(),
         ty       char(2), -- Type of edit. Insert, delete, alter
         si       integer, -- Start index for deletion
         ei       integer, -- End index for deletion
         ibi      integer, -- Insert index
         s        text,    -- Text to insert
         ft       text     -- For debugging: Ongoing reconstruction of full text
  );
  
  CREATE OR REPLACE FUNCTION insert_writing_delta(
         gusername text,
         gdocstring char(48),
         ty        char(2), -- Type of edit. Insert, delete, alter
         si        integer, -- Start index for deletion
         ei        integer, -- End index for deletion
         ibi       integer, -- Insert index
         s         text,    -- Text to insert
         ft        text     -- For debugging: Ongoing reconstruction of full text
  ) RETURNS text
  LANGUAGE plpgsql
  AS $$
  DECLARE
    strresult text;
    affected_rows integer;
  BEGIN
    strresult := '';
    -- If the user does not exist, create the user. Add 'New User' to the return value
    if NOT EXISTS (SELECT 1 FROM USERS where USERS.username = gusername) THEN
      strresult := strresult || '[New User]';
      INSERT INTO USERS (username) VALUES (gusername);
    END IF;
    
    -- If the document does not exist, create the document. Add "New Document" to the return value
    if NOT EXISTS (SELECT 1 FROM DOCUMENTS where DOCUMENTS.docstring = gdocstring) THEN
      strresult := strresult || '[New Document]';
      INSERT INTO DOCUMENTS (docstring) VALUES (gdocstring);
    END IF;
    -- Insert the writing delta into the database
    with INSERT_ROW_COUNT as
       (INSERT INTO WRITING_DELTAS
         (user_id, document, ty, si, ei, ibi, s, ft)
         (SELECT
              users.idx, documents.idx, ty, si, ei, ibi, s, ft
          FROM
             users, documents where users.username=gusername and documents.docstring=gdocstring)
          RETURNING 1)
       SELECT COUNT(*) INTO affected_rows FROM INSERT_ROW_COUNT;
    
    -- This is a little bit awkward, but we return:
    -- 1. Number of rows inserted
    -- 2. Whether a new user or document was created
    -- As a string.
    return cast(affected_rows as varchar) || ' ' || strresult;
    COMMIT;
  END;
  $$;
  -- Example: SELECT insert_writing_delta('pmitros', 'random-google-doc-id', 'is', 7,8,4,'hello','temp');

stored_procedures:
  insert_writing_delta: |
    -- PREPARE insert_writing_delta (text, char(48), char(2), integer, integer, integer, text, text) AS
      SELECT insert_writing_delta($1, $2, $3, $4, $5, $6, $7, $8);

  fetch_writing_deltas: |
    -- PREPARE fetch_writing_deltas (text, char(48)) AS  -- username, document string
      SELECT
        WRITING_DELTAS.idx, WRITING_DELTAS.date_created, ty, si, ei, ibi, s, ft
      FROM
        WRITING_DELTAS, USERS, DOCUMENTS
      WHERE
        WRITING_DELTAS.user_id = USERS.idx AND
        WRITING_DELTAS.document = DOCUMENTS.idx AND
        DOCUMENTS.docstring = $2 AND
        USERS.username = $1
      ORDER BY
        WRITING_DELTAS.idx;
