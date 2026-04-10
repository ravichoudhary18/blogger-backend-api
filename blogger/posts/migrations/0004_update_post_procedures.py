from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("posts", "0003_post_procedures"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE PROCEDURE add_post(
                p_title VARCHAR, 
                p_content TEXT, 
                p_author_id INT, 
                p_status VARCHAR,
                p_created_at TIMESTAMP WITH TIME ZONE,
                p_updated_at TIMESTAMP WITH TIME ZONE
            )
            LANGUAGE plpgsql
            AS $$
            BEGIN
                INSERT INTO posts_post (
                    title, content, author_id, status, 
                    created_by_id, updated_by_id, 
                    created_at, updated_at
                )
                VALUES (
                    p_title, p_content, p_author_id, p_status, 
                    p_author_id, p_author_id, 
                    p_created_at, p_updated_at
                );
            END;
            $$;
            """,
            reverse_sql="DROP PROCEDURE IF EXISTS add_post(VARCHAR, TEXT, INT, VARCHAR, TIMESTAMP WITH TIME ZONE, TIMESTAMP WITH TIME ZONE);",
        ),
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE PROCEDURE update_post(
                p_post_id INT, 
                p_title VARCHAR, 
                p_content TEXT, 
                p_status VARCHAR, 
                p_updated_by_id INT,
                p_updated_at TIMESTAMP WITH TIME ZONE
            )
            LANGUAGE plpgsql
            AS $$
            BEGIN
                UPDATE posts_post
                SET title = p_title,
                    content = p_content,
                    status = p_status,
                    updated_by_id = p_updated_by_id,
                    updated_at = p_updated_at
                WHERE id = p_post_id;
            END;
            $$;
            """,
            reverse_sql="DROP PROCEDURE IF EXISTS update_post(INT, VARCHAR, TEXT, VARCHAR, INT, TIMESTAMP WITH TIME ZONE);",
        ),
    ]
