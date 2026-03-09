"""
Community Forum for Farmer-to-Farmer Q&A
Simple discussion board using DynamoDB
"""

from datetime import datetime
from typing import Dict, List, Optional
from shared.dynamodb_repository import DynamoDBRepository


class CommunityForum:
    """Community forum for farmer discussions"""
    
    def __init__(self, db_repo: DynamoDBRepository):
        """Initialize forum with DynamoDB repository"""
        self.db = db_repo
        self.categories = [
            "Crop Diseases",
            "Pest Control",
            "Fertilizers",
            "Irrigation",
            "Market Prices",
            "Government Schemes",
            "Weather & Climate",
            "Organic Farming",
            "General Discussion"
        ]
    
    def post_question(self, user_id: str, question: Dict) -> str:
        """Post a new question to the forum"""
        timestamp = datetime.utcnow().isoformat()
        question_id = f"Q#{timestamp}"
        
        item = {
            'PK': 'FORUM#QUESTIONS',
            'SK': question_id,
            'user_id': user_id,
            'title': question['title'],
            'description': question['description'],
            'category': question.get('category', 'General Discussion'),
            'language': question.get('language', 'en'),
            'created_at': timestamp,
            'answer_count': 0,
            'views': 0,
            'status': 'open'  # open, answered, closed
        }
        
        self.db.table.put_item(Item=item)
        return question_id
    
    def post_answer(self, user_id: str, question_id: str, answer: Dict) -> str:
        """Post an answer to a question"""
        timestamp = datetime.utcnow().isoformat()
        answer_id = f"A#{timestamp}"
        
        item = {
            'PK': f'FORUM#{question_id}',
            'SK': answer_id,
            'user_id': user_id,
            'answer_text': answer['answer_text'],
            'created_at': timestamp,
            'helpful_count': 0
        }
        
        self.db.table.put_item(Item=item)
        
        # Increment answer count on question
        try:
            self.db.table.update_item(
                Key={
                    'PK': 'FORUM#QUESTIONS',
                    'SK': question_id
                },
                UpdateExpression='SET answer_count = answer_count + :inc',
                ExpressionAttributeValues={':inc': 1}
            )
        except:
            pass
        
        return answer_id
    
    def get_questions(self, category: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """Get list of questions, optionally filtered by category"""
        try:
            response = self.db.table.query(
                KeyConditionExpression='PK = :pk',
                ExpressionAttributeValues={':pk': 'FORUM#QUESTIONS'},
                ScanIndexForward=False,
                Limit=limit
            )
            
            questions = self.db._convert_decimals(response.get('Items', []))
            
            # Filter by category if specified
            if category and category != "All":
                questions = [q for q in questions if q.get('category') == category]
            
            return questions
        except Exception as e:
            print(f"Error getting questions: {e}")
            return []
    
    def get_question_with_answers(self, question_id: str) -> Dict:
        """Get a question and all its answers"""
        try:
            # Get question
            question_response = self.db.table.get_item(
                Key={
                    'PK': 'FORUM#QUESTIONS',
                    'SK': question_id
                }
            )
            
            question = self.db._convert_decimals(question_response.get('Item', {}))
            
            if not question:
                return {}
            
            # Get answers
            answers_response = self.db.table.query(
                KeyConditionExpression='PK = :pk',
                ExpressionAttributeValues={':pk': f'FORUM#{question_id}'},
                ScanIndexForward=True
            )
            
            answers = self.db._convert_decimals(answers_response.get('Items', []))
            
            # Increment view count
            try:
                self.db.table.update_item(
                    Key={
                        'PK': 'FORUM#QUESTIONS',
                        'SK': question_id
                    },
                    UpdateExpression='SET #views = #views + :inc',
                    ExpressionAttributeNames={'#views': 'views'},
                    ExpressionAttributeValues={':inc': 1}
                )
            except:
                pass
            
            return {
                'question': question,
                'answers': answers
            }
        except Exception as e:
            print(f"Error getting question with answers: {e}")
            return {}
    
    def mark_answer_helpful(self, question_id: str, answer_id: str) -> bool:
        """Mark an answer as helpful"""
        try:
            self.db.table.update_item(
                Key={
                    'PK': f'FORUM#{question_id}',
                    'SK': answer_id
                },
                UpdateExpression='SET helpful_count = helpful_count + :inc',
                ExpressionAttributeValues={':inc': 1}
            )
            return True
        except Exception as e:
            print(f"Error marking answer helpful: {e}")
            return False
    
    def get_categories(self) -> List[str]:
        """Get list of forum categories"""
        return self.categories
    
    def search_questions(self, search_term: str, limit: int = 20) -> List[Dict]:
        """Search questions by title or description"""
        questions = self.get_questions(limit=limit)
        
        search_lower = search_term.lower()
        filtered = [
            q for q in questions
            if search_lower in q.get('title', '').lower() or 
               search_lower in q.get('description', '').lower()
        ]
        
        return filtered


# Global instance
_community_forum: CommunityForum = None


def get_community_forum(db_repo: DynamoDBRepository) -> CommunityForum:
    """Get community forum instance"""
    global _community_forum
    
    if _community_forum is None:
        _community_forum = CommunityForum(db_repo)
    
    return _community_forum


if __name__ == '__main__':
    # Test community forum
    from shared.dynamodb_repository import DynamoDBRepository
    
    db = DynamoDBRepository()
    forum = get_community_forum(db)
    
    print("Community Forum Test")
    print("=" * 50)
    print(f"Categories: {', '.join(forum.get_categories())}")
