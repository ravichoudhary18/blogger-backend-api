from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("posts", "0005_post_delete_status_procedures"),
    ]

    operations = [
        # Function to get a single post by ID (public only)
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION get_post_by_id(p_post_id INT)
            RETURNS JSON
            LANGUAGE plpgsql
            AS $$
            DECLARE
                result JSON;
            BEGIN
                SELECT json_build_object(
                    'id', p.id,
                    'title', p.title,
                    'content', p.content,
                    'status', p.status,
                    'author', p.author_id,
                    'author_username', u.username,
                    'likes_count', (SELECT COUNT(*) FROM interaction_like WHERE post_id = p.id),
                    'comments_count', (SELECT COUNT(*) FROM interaction_comment WHERE post_id = p.id),
                    'share_count', (SELECT COUNT(*) FROM interaction_share WHERE post_id = p.id),
                    'created_at', p.created_at,
                    'updated_at', p.updated_at
                ) INTO result
                FROM posts_post p
                JOIN auth_user u ON u.id = p.author_id
                WHERE p.id = p_post_id AND p.status = 'public';

                RETURN result;
            END;
            $$;
            """,
            reverse_sql="DROP FUNCTION IF EXISTS get_post_by_id(INT);",
        ),
        # Function to get filtered posts list
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION get_posts(
                p_title VARCHAR DEFAULT NULL,
                p_author VARCHAR DEFAULT NULL,
                p_start_date DATE DEFAULT NULL,
                p_end_date DATE DEFAULT NULL,
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
                -- Get total count for pagination
                SELECT COUNT(*) INTO total_count
                FROM posts_post p
                JOIN auth_user u ON u.id = p.author_id
                WHERE p.status = 'public'
                  AND (p_title IS NULL OR p.title ILIKE '%' || p_title || '%')
                  AND (p_author IS NULL OR u.username ILIKE '%' || p_author || '%')
                  AND (p_start_date IS NULL OR p.created_at::date >= p_start_date)
                  AND (p_end_date IS NULL OR p.created_at::date <= p_end_date);

                -- Get paginated results with counts
                SELECT json_build_object(
                    'count', total_count,
                    'results', COALESCE(
                        (SELECT json_agg(post_row)
                         FROM (
                            SELECT
                                p.id,
                                p.title,
                                p.content,
                                p.status,
                                p.author_id AS author,
                                u.username AS author_username,
                                (SELECT COUNT(*) FROM interaction_like WHERE post_id = p.id) AS likes_count,
                                (SELECT COUNT(*) FROM interaction_comment WHERE post_id = p.id) AS comments_count,
                                (SELECT COUNT(*) FROM interaction_share WHERE post_id = p.id) AS share_count,
                                p.created_at,
                                p.updated_at
                            FROM posts_post p
                            JOIN auth_user u ON u.id = p.author_id
                            WHERE p.status = 'public'
                              AND (p_title IS NULL OR p.title ILIKE '%' || p_title || '%')
                              AND (p_author IS NULL OR u.username ILIKE '%' || p_author || '%')
                              AND (p_start_date IS NULL OR p.created_at::date >= p_start_date)
                              AND (p_end_date IS NULL OR p.created_at::date <= p_end_date)
                            ORDER BY p.created_at DESC
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
            reverse_sql="DROP FUNCTION IF EXISTS get_posts(VARCHAR, VARCHAR, DATE, DATE, INT, INT);",
        ),
    ]
