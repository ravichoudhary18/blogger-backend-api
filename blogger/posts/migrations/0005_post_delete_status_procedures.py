from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("posts", "0004_update_post_procedures"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE PROCEDURE delete_post(p_post_id INT)
            LANGUAGE plpgsql
            AS $$
            BEGIN
                DELETE FROM posts_post WHERE id = p_post_id;
            END;
            $$;
            """,
            reverse_sql="DROP PROCEDURE IF EXISTS delete_post(INT);",
        ),
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE PROCEDURE update_post_status(
                p_post_id INT, 
                p_status VARCHAR, 
                p_updated_by_id INT,
                p_updated_at TIMESTAMP WITH TIME ZONE
            )
            LANGUAGE plpgsql
            AS $$
            BEGIN
                UPDATE posts_post
                SET status = p_status,
                    updated_by_id = p_updated_by_id,
                    updated_at = p_updated_at
                WHERE id = p_post_id;
            END;
            $$;
            """,
            reverse_sql="DROP PROCEDURE IF EXISTS update_post_status(INT, VARCHAR, INT, TIMESTAMP WITH TIME ZONE);",
        ),
    ]
