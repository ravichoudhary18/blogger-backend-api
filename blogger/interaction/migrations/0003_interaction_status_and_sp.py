from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("interaction", "0002_interaction_get_functions"),
    ]

    operations = [
        migrations.AddField(
            model_name="comment",
            name="status",
            field=models.CharField(
                choices=[("active", "active"), ("deleted", "deleted")],
                default="active",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="like",
            name="status",
            field=models.CharField(
                choices=[("active", "active"), ("deleted", "deleted")],
                default="active",
                max_length=10,
            ),
        ),
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION get_comments_by_post(
                p_post_id INT,
                p_limit INT DEFAULT 10,
                p_offset INT DEFAULT 0
            )
            RETURNS JSON
            LANGUAGE plpgsql
            AS $$
            DECLARE
                result JSON;
                total_count INT;
            BEGIN
                SELECT COUNT(*) INTO total_count
                FROM interaction_comment
                WHERE post_id = p_post_id AND status = 'active';

                SELECT json_build_object(
                    'count', total_count,
                    'results', COALESCE(
                        (SELECT json_agg(comment_row)
                         FROM (
                            SELECT
                                c.id,
                                c.post_id AS post,
                                c.user_id AS user,
                                u.username AS username,
                                c.content,
                                c.created_at
                            FROM interaction_comment c
                            JOIN auth_user u ON u.id = c.user_id
                            WHERE c.post_id = p_post_id AND c.status = 'active'
                            ORDER BY c.created_at DESC
                            LIMIT p_limit
                            OFFSET p_offset
                         ) comment_row),
                        '[]'::json
                    )
                ) INTO result;

                RETURN result;
            END;
            $$;
            """,
            reverse_sql="""
            CREATE OR REPLACE FUNCTION get_comments_by_post(
                p_post_id INT,
                p_limit INT DEFAULT 10,
                p_offset INT DEFAULT 0
            )
            RETURNS JSON
            LANGUAGE plpgsql
            AS $$
            DECLARE
                result JSON;
                total_count INT;
            BEGIN
                SELECT COUNT(*) INTO total_count
                FROM interaction_comment
                WHERE post_id = p_post_id;

                SELECT json_build_object(
                    'count', total_count,
                    'results', COALESCE(
                        (SELECT json_agg(comment_row)
                         FROM (
                            SELECT
                                c.id,
                                c.post_id AS post,
                                c.user_id AS user,
                                u.username AS username,
                                c.content,
                                c.created_at
                            FROM interaction_comment c
                            JOIN auth_user u ON u.id = c.user_id
                            WHERE c.post_id = p_post_id
                            ORDER BY c.created_at DESC
                            LIMIT p_limit
                            OFFSET p_offset
                         ) comment_row),
                        '[]'::json
                    )
                ) INTO result;

                RETURN result;
            END;
            $$;
            """
        ),
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION get_likes_by_post(
                p_post_id INT,
                p_limit INT DEFAULT 10,
                p_offset INT DEFAULT 0
            )
            RETURNS JSON
            LANGUAGE plpgsql
            AS $$
            DECLARE
                result JSON;
                total_count INT;
            BEGIN
                SELECT COUNT(*) INTO total_count
                FROM interaction_like
                WHERE post_id = p_post_id AND status = 'active';

                SELECT json_build_object(
                    'count', total_count,
                    'results', COALESCE(
                        (SELECT json_agg(like_row)
                         FROM (
                            SELECT
                                l.id,
                                l.post_id AS post,
                                l.user_id AS user,
                                u.username AS username,
                                l.created_at
                            FROM interaction_like l
                            JOIN auth_user u ON u.id = l.user_id
                            WHERE l.post_id = p_post_id AND l.status = 'active'
                            ORDER BY l.created_at DESC
                            LIMIT p_limit
                            OFFSET p_offset
                         ) like_row),
                        '[]'::json
                    )
                ) INTO result;

                RETURN result;
            END;
            $$;
            """,
            reverse_sql="""
            CREATE OR REPLACE FUNCTION get_likes_by_post(
                p_post_id INT,
                p_limit INT DEFAULT 10,
                p_offset INT DEFAULT 0
            )
            RETURNS JSON
            LANGUAGE plpgsql
            AS $$
            DECLARE
                result JSON;
                total_count INT;
            BEGIN
                SELECT COUNT(*) INTO total_count
                FROM interaction_like
                WHERE post_id = p_post_id;

                SELECT json_build_object(
                    'count', total_count,
                    'results', COALESCE(
                        (SELECT json_agg(like_row)
                         FROM (
                            SELECT
                                l.id,
                                l.post_id AS post,
                                l.user_id AS user,
                                u.username AS username,
                                l.created_at
                            FROM interaction_like l
                            JOIN auth_user u ON u.id = l.user_id
                            WHERE l.post_id = p_post_id
                            ORDER BY l.created_at DESC
                            LIMIT p_limit
                            OFFSET p_offset
                         ) like_row),
                        '[]'::json
                    )
                ) INTO result;

                RETURN result;
            END;
            $$;
            """
        ),
    ]
