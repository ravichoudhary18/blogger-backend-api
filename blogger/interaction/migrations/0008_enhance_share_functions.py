from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("interaction", "0007_fix_ambiguous_user_id"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            -- Update get_shares_by_post to include shared_with recipient IDs
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
                                s.created_at,
                                COALESCE(
                                    (SELECT json_agg(j.user_id)
                                     FROM interaction_share_shared_with j
                                     WHERE j.share_id = s.id),
                                    '[]'::json
                                ) AS shared_with
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

            -- Update get_shared_posts_by_user to include shared_with recipient IDs
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
                v_user_id INT;
            BEGIN
                SELECT id INTO v_user_id FROM auth_user WHERE username = p_username;
                
                IF v_user_id IS NULL THEN
                    RETURN json_build_object('count', 0, 'results', '[]'::json);
                END IF;

                SELECT COUNT(*) INTO total_count
                FROM interaction_share s
                JOIN posts_post p ON p.id = s.post_id
                WHERE s.user_id = v_user_id AND p.status = 'public';

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
                                COALESCE(
                                    (SELECT json_agg(j.user_id)
                                     FROM interaction_share_shared_with j
                                     WHERE j.share_id = s.id),
                                    '[]'::json
                                ) AS shared_with
                            FROM interaction_share s
                            JOIN posts_post p ON p.id = s.post_id
                            JOIN auth_user u ON u.id = p.author_id
                            WHERE s.user_id = v_user_id AND p.status = 'public'
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
            reverse_sql="",
        ),
    ]
