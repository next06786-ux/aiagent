/**
 * Markdown
 * Markdown
 */

export interface MarkdownBlock {
  type: 'heading' | 'paragraph' | 'list' | 'code' | 'bold' | 'text';
  content: string;
  level?: number; // 处理逻辑
  items?: string[]; // 处理逻辑
}

export interface InlinePart {
  text: string;
  bold: boolean;
}

export class MarkdownParser {
  /**
   * Markdown
   */
  static parse(markdown: string): MarkdownBlock[] {
    const blocks: MarkdownBlock[] = [];
    const lines = markdown.split('\n');
    
    let i = 0;
    while (i < lines.length) {
      const line = lines[i];
      
      // 处理逻辑
      if (!line.trim()) {
        i++;
        continue;
      }
      
      //  (# ## ###)
      if (line.startsWith('#')) {
        const match = line.match(/^(#{1,6})\s+(.+)$/);
        if (match) {
          blocks.push({
            type: 'heading',
            content: match[2],
            level: match[1].length
          });
          i++;
          continue;
        }
      }
      
      //  (-  *)
      if (line.match(/^[\-\*]\s+/)) {
        const items: string[] = [];
        while (i < lines.length && lines[i].match(/^[\-\*]\s+/)) {
          items.push(lines[i].replace(/^[\-\*]\s+/, ''));
          i++;
        }
        blocks.push({
          type: 'list',
          content: '',
          items: items
        });
        continue;
      }
      
      //  (1. 2. 3.)
      if (line.match(/^\d+\.\s+/)) {
        const items: string[] = [];
        while (i < lines.length && lines[i].match(/^\d+\.\s+/)) {
          items.push(lines[i].replace(/^\d+\.\s+/, ''));
          i++;
        }
        blocks.push({
          type: 'list',
          content: '',
          items: items
        });
        continue;
      }
      
      //  (```)
      if (line.startsWith('```')) {
        const codeLines: string[] = [];
        i++; // ```
        while (i < lines.length && !lines[i].startsWith('```')) {
          codeLines.push(lines[i]);
          i++;
        }
        i++; // ```
        blocks.push({
          type: 'code',
          content: codeLines.join('\n')
        });
        continue;
      }
      
      // 处理逻辑
      blocks.push({
        type: 'paragraph',
        content: line
      });
      i++;
    }
    
    return blocks;
  }
  
  /**
 * 服务类
 */
  static parseInline(text: string): InlinePart[] {
    const result: InlinePart[] = [];
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    
    for (const part of parts) {
      if (part.startsWith('**') && part.endsWith('**')) {
        // 处理逻辑
        const inlinePart: InlinePart = {
          text: part.slice(2, -2),
          bold: true
        };
        result.push(inlinePart);
      } else if (part) {
        // 处理逻辑
        const inlinePart: InlinePart = {
          text: part,
          bold: false
        };
        result.push(inlinePart);
      }
    }
    
    return result;
  }
}
