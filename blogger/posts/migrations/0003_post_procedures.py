from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("posts", "0002_alter_post_status"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE PROCEDURE add_post(
                p_title VARCHAR, 
                p_content TEXT, 
                p_author_id INT, 
                p_status VARCHAR
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
                    NOW(), NOW()
                );
            END;
            $$;
            """,
            reverse_sql="DROP PROCEDURE IF EXISTS add_post(VARCHAR, TEXT, INT, VARCHAR);",
        ),
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE PROCEDURE update_post(
                p_post_id INT, 
                p_title VARCHAR, 
                p_content TEXT, 
                p_status VARCHAR, 
                p_updated_by_id INT
            )
            LANGUAGE plpgsql
            AS $$
            BEGIN
                UPDATE posts_post
                SET title = p_title,
                    content = p_content,
                    status = p_status,
                    updated_by_id = p_updated_by_id,
                    updated_at = NOW()
                WHERE id = p_post_id;
            END;
            $$;
            """,
            reverse_sql="DROP PROCEDURE IF EXISTS update_post(INT, VARCHAR, TEXT, VARCHAR, INT);",
        ),
    ]
