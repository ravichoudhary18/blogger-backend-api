from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("posts", "0010_post_thumbnail_document"),
    ]

    operations = [
        # Drop the procedure
        migrations.RunSQL(
            sql="DROP PROCEDURE IF EXISTS add_post(VARCHAR, TEXT, INT, VARCHAR, TIMESTAMP WITH TIME ZONE, TIMESTAMP WITH TIME ZONE, VARCHAR);",
            reverse_sql=""
        ),
        # Create a function instead
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION add_post(
                p_title VARCHAR, 
                p_content TEXT, 
                p_author_id INT, 
                p_status VARCHAR,
                p_created_at TIMESTAMP WITH TIME ZONE,
                p_updated_at TIMESTAMP WITH TIME ZONE,
                p_thumbnail VARCHAR DEFAULT NULL
            )
            RETURNS INT
            LANGUAGE plpgsql
            AS $$
            DECLARE
                new_id INT;
            BEGIN
                INSERT INTO posts_post (
                    title, content, author_id, status, 
                    created_by_id, updated_by_id, 
                    created_at, updated_at, thumbnail
                )
                VALUES (
                    p_title, p_content, p_author_id, p_status, 
                    p_author_id, p_author_id, 
                    p_created_at, p_updated_at, p_thumbnail
                )
                RETURNING id INTO new_id;
                
                RETURN new_id;
            END;
            $$;
            """,
            reverse_sql="DROP FUNCTION IF EXISTS add_post(VARCHAR, TEXT, INT, VARCHAR, TIMESTAMP WITH TIME ZONE, TIMESTAMP WITH TIME ZONE, VARCHAR);",
        ),
    ]
