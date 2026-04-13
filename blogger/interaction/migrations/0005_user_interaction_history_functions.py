from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("interaction", "0004_merge_20260410_1840"),
    ]

    operations = [
        # Function to get posts liked by a specific user
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION get_liked_posts_by_user(
                p_username VARCHAR,
                p_limit INT DEFAULT 10,
                p_offset INT DEFAULT 0
            )
            RETURNS JSON
            LANGUAGE plpgsql
            AS $$
            DECLARE
                result JSON;
                total_count INT;
                user_id INT;
            BEGIN
                SELECT id INTO user_id FROM auth_user WHERE username = p_username;
                
                IF user_id IS NULL THEN
                    RETURN json_build_object('count', 0, 'results', '[]'::json);
                END IF;

                SELECT COUNT(*) INTO total_count
                FROM interaction_like l
                JOIN posts_post p ON p.id = l.post_id
                WHERE l.user_id = user_id AND l.status = 'active' AND p.status = 'public';

                SELECT json_build_object(
                    'count', total_count,
                    'results', COALESCE(
                        (SELECT json_agg(post_row)
                         FROM (
                            SELECT
                                p.id,
                                p.title,
                                p.content,
                                p.author_id AS author,
                                u.username AS author_username,
                                p.thumbnail,
                                p.created_at,
                                p.updated_at
                            FROM interaction_like l
                            JOIN posts_post p ON p.id = l.post_id
                            JOIN auth_user u ON u.id = p.author_id
                            WHERE l.user_id = user_id AND l.status = 'active' AND p.status = 'public'
                            ORDER BY l.created_at DESC
                            LIMIT p_limit
                            OFFSET p_offset
                         ) post_row),
                        '[]'::json
                    )
                ) INTO result;

                RETURN result;
            END;
            $$;
            """,
            reverse_sql="DROP FUNCTION IF EXISTS get_liked_posts_by_user(VARCHAR, INT, INT);",
        ),
        # Function to get posts commented on by a specific user
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION get_commented_posts_by_user(
                p_username VARCHAR,
                p_limit INT DEFAULT 10,
                p_offset INT DEFAULT 0
            )
            RETURNS JSON
            LANGUAGE plpgsql
            AS $$
            DECLARE
                result JSON;
                total_count INT;
                user_id INT;
            BEGIN
                SELECT id INTO user_id FROM auth_user WHERE username = p_username;
                
                IF user_id IS NULL THEN
                    RETURN json_build_object('count', 0, 'results', '[]'::json);
                END IF;

                -- Using DISTINCT because a user might comment multiple times on the same post
                SELECT COUNT(DISTINCT post_id) INTO total_count
                FROM interaction_comment c
                JOIN posts_post p ON p.id = c.post_id
                WHERE c.user_id = user_id AND c.status = 'active' AND p.status = 'public';

                SELECT json_build_object(
                    'count', total_count,
                    'results', COALESCE(
                        (SELECT json_agg(post_row)
                         FROM (
                            SELECT
                                p.id,
                                p.title,
                                p.content,
                                p.author_id AS author,
                                u.username AS author_username,
                                p.thumbnail,
                                p.created_at,
                                p.updated_at,
                                MAX(c.created_at) as last_commented_at
                            FROM interaction_comment c
                            JOIN posts_post p ON p.id = c.post_id
                            JOIN auth_user u ON u.id = p.author_id
                            WHERE c.user_id = user_id AND c.status = 'active' AND p.status = 'public'
                            GROUP BY p.id, u.username
                            ORDER BY last_commented_at DESC
                            LIMIT p_limit
                            OFFSET p_offset
                         ) post_row),
                        '[]'::json
                    )
                ) INTO result;

                RETURN result;
            END;
            $$;
            """,
            reverse_sql="DROP FUNCTION IF EXISTS get_commented_posts_by_user(VARCHAR, INT, INT);",
        ),
        # Function to get posts shared by a specific user
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION get_shared_posts_by_user(
                p_username VARCHAR,
                p_limit INT DEFAULT 10,
                p_offset INT DEFAULT 0
            )
            RETURNS JSON
            LANGUAGE plpgsql
            AS $$
            DECLARE
                result JSON;
                total_count INT;
                user_id INT;
            BEGIN
                SELECT id INTO user_id FROM auth_user WHERE username = p_username;
                
                IF user_id IS NULL THEN
                    RETURN json_build_object('count', 0, 'results', '[]'::json);
                END IF;

                SELECT COUNT(*) INTO total_count
                FROM interaction_share s
                JOIN posts_post p ON p.id = s.post_id
                WHERE s.user_id = user_id AND p.status = 'public';

                SELECT json_build_object(
                    'count', total_count,
                    'results', COALESCE(
                        (SELECT json_agg(post_row)
                         FROM (
                            SELECT
                                p.id,
                                p.title,
                                p.content,
                                p.author_id AS author,
                                u.username AS author_username,
                                p.thumbnail,
                                p.created_at,
                                p.updated_at
                            FROM interaction_share s
                            JOIN posts_post p ON p.id = s.post_id
                            JOIN auth_user u ON u.id = p.author_id
                            WHERE s.user_id = user_id AND p.status = 'public'
                            ORDER BY s.created_at DESC
                            LIMIT p_limit
                            OFFSET p_offset
                         ) post_row),
                        '[]'::json
                    )
                ) INTO result;

                RETURN result;
            END;
            $$;
            """,
            reverse_sql="DROP FUNCTION IF EXISTS get_shared_posts_by_user(VARCHAR, INT, INT);",
        ),
    ]
