from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("interaction", "0001_initial"),
    ]

    operations = [
        # Function for comments
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
            """,
            reverse_sql="DROP FUNCTION IF EXISTS get_comments_by_post(INT, INT, INT);",
        ),
        # Function for likes
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
            """,
            reverse_sql="DROP FUNCTION IF EXISTS get_likes_by_post(INT, INT, INT);",
        ),
        # Function for shares
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION get_shares_by_post(
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
                FROM interaction_share
                WHERE post_id = p_post_id;

                SELECT json_build_object(
                    'count', total_count,
                    'results', COALESCE(
                        (SELECT json_agg(share_row)
                         FROM (
                            SELECT
                                s.id,
                                s.post_id AS post,
                                s.user_id AS user,
                                u.username AS username,
                                s.platform,
                                s.created_at
                            FROM interaction_share s
                            JOIN auth_user u ON u.id = s.user_id
                            WHERE s.post_id = p_post_id
                            ORDER BY s.created_at DESC
                            LIMIT p_limit
                            OFFSET p_offset
                         ) share_row),
                        '[]'::json
                    )
                ) INTO result;

                RETURN result;
            END;
            $$;
            """,
            reverse_sql="DROP FUNCTION IF EXISTS get_shares_by_post(INT, INT, INT);",
        ),
    ]
